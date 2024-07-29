"""
Original © NetApp 2024

This is the implementation of an async command for the recline library. It allows
for a command to be run in the foreground or background.
"""

import asyncio
from contextlib import contextmanager
import io
import os
import signal
import sys
from threading import Thread
import time
from typing import Any

import recline


class CommandBackgrounded(Exception):
    """When a command is moved from the foreground to the background, this exception
    is raised to signal the shell.
    """

    def __init__(self, job_pid, *args, **kwargs):
        self.job_pid = job_pid
        super().__init__(*args, **kwargs)


class CommandCancelled(Exception):
    """When a command is cancelled, this is exception is raised to signal the shell"""

    def __init__(self, job_pid, *args, **kwargs):
        self.job_pid = job_pid
        super().__init__(*args, **kwargs)


# pylint: disable=too-many-instance-attributes
class AsyncCommand(Thread):
    """This is a custom Thread class meant to wrap an asynchronous recline command.

    It provides the ability to gather a result as well as put the thread in the
    foreground or the background of the main REPL thread.
    """

    def __init__(self, command, *args, **kwargs):
        super().__init__()

        self.result = None
        self.exception = None
        self.command = command
        self.job_pid = recline.NEXT_JOB_PID
        recline.JOBS[self.job_pid] = self
        recline.NEXT_JOB_PID += 1

        self._args = args
        self._kwargs = kwargs
        self._loop = asyncio.new_event_loop()
        self._task = None
        self._wait = True
        self._killed = False
        self._orig_sigint_handler = None
        self._orig_sigstp_handler = None

    def run(self) -> None:
        """Start the command in an asyncio loop. When it's complete, the result
        will be recorded in this thread
        """

        if sys.platform != "win32":
            self._orig_sigstp_handler = signal.getsignal(signal.SIGTSTP)
        self._orig_sigint_handler = signal.getsignal(signal.SIGINT)
        asyncio.set_event_loop(self._loop)
        self._task = asyncio.ensure_future(self.command.func(*self._args, **self._kwargs))
        try:
            self.result = self._loop.run_until_complete(self._task)
        except Exception as ex:  # pylint: disable=broad-except
            self.exception = ex

    def stop(self, dont_delete=False) -> None:
        """Kill the command and return control to the main thread"""

        self._task.cancel()
        signal.signal(signal.SIGINT, self._orig_sigint_handler)
        self._killed = True
        if dont_delete:
            return
        del recline.JOBS[self.job_pid]

    def background(self) -> None:
        """Unblock the calling thread and put this thread into the background"""

        self._wait = False
        if sys.platform != "win32":
            signal.signal(signal.SIGTSTP, self._orig_sigstp_handler)

    def foreground(self) -> Any:
        """Block the calling thread until this thread is complete and return the result

        Also setup up a signal handler for SIGTSTP so that pressing ctrl+z will
        put this thread in the background
        """

        self._wait = True
        with self._manipulate_signals(), set_terminal_echo(enabled=False):
            while self._wait and self.is_alive():
                time.sleep(.01)
            if self._killed:
                raise CommandCancelled(self.job_pid)
            if not self._wait:
                raise CommandBackgrounded(self.job_pid)
            if self.exception:
                del recline.JOBS[self.job_pid]
                raise self.exception
            return recline.JOBS.pop(self.job_pid).result

    @contextmanager
    def _manipulate_signals(self):
        if sys.platform != "win32":
            signal.signal(
                signal.SIGTSTP,
                lambda signum, frame: self.background(),
            )
        signal.signal(
            signal.SIGINT,
            lambda signum, frame: self.stop(),
        )
        yield
        if sys.platform != "win32":
            signal.signal(signal.SIGTSTP, self._orig_sigstp_handler)
        signal.signal(signal.SIGINT, self._orig_sigint_handler)


@contextmanager
def set_terminal_echo(enabled=True):
    """ Code from https://docs.python.org/2/library/termios.html """

    try:
        import termios
    except ImportError:
        # must be a Windows system. There's no terios module there, so there's
        # nothing we can do here
        yield
        return

    # in something like pytest, stdin might not have a fileno
    try:
        stdin = sys.stdin.fileno()
    except io.UnsupportedOperation:
        yield
        return

    # if we're not running interactively, then there's no need (or ability) to
    # change the echo status
    if not os.isatty(stdin):
        yield
        return

    old = termios.tcgetattr(stdin)
    new = termios.tcgetattr(stdin)
    if not enabled:
        new[3] = new[3] & ~termios.ECHO
    else:
        new[3] = new[3] | termios.ECHO
    try:
        termios.tcsetattr(stdin, termios.TCSADRAIN, new)
        yield
    finally:
        termios.tcsetattr(stdin, termios.TCSADRAIN, old)
