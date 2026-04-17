"""
Original © NetApp 2024

A test module for the recline.commands.async_command module
"""

import asyncio
import os
import sys
import termios
import threading
import time

import pytest

import recline
from recline.commands.async_command import (
    AsyncCommand,
    CommandBackgrounded,
    CommandCancelled,
    set_terminal_echo,
)


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_run():
    """Verify that if given a coroutine, the AsyncCommand will register and then
    run the coroutine when in the foreground.
    """

    test_result = "This is the answer"

    @recline.command(name="test")
    async def test_coro():
        return test_result

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    job_pid = thread.job_pid
    assert recline.JOBS[job_pid] == thread
    assert recline.NEXT_JOB_PID == job_pid + 1
    thread.start()
    assert thread.foreground() == test_result
    assert job_pid not in recline.JOBS


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_run_background():
    """Verify that if given a coroutine, the AsyncCommand will register and then
    run the coroutine when in the background and we can retrieve the result.
    """

    test_result = "This is the answer"

    @recline.command(name="test")
    async def test_coro():
        return test_result

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    thread.start()
    thread.background()
    # wait until it is complete
    while thread.is_alive():
        pass
    assert thread.result == test_result


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_stop():
    """Verify that we can kill a long running command"""

    i_was_stopped = False
    i_was_started = False

    @recline.command(name="test")
    async def test_coro():
        nonlocal i_was_stopped, i_was_started
        try:
            while True:
                i_was_started = True
                await asyncio.sleep(0.001)
        except asyncio.CancelledError:
            i_was_stopped = True

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    job_pid = thread.job_pid
    thread.start()
    # wait until it is started
    while not i_was_started:
        pass
    thread.stop()
    # wait until it is stopped
    while thread.is_alive():
        pass
    assert i_was_stopped
    assert job_pid not in recline.JOBS


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_exception():
    """Verify that an exception thrown in the background thread is raised to the
    foreground thread when it is foregrounded
    """

    test_result = "This is the exception"

    @recline.command(name="test")
    async def test_coro():
        raise RuntimeError(test_result)

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    job_pid = thread.job_pid
    assert recline.JOBS[job_pid] == thread
    assert recline.NEXT_JOB_PID == job_pid + 1
    thread.start()
    with pytest.raises(RuntimeError, match=test_result):
        assert thread.foreground() == test_result
    assert job_pid not in recline.JOBS


@pytest.mark.usefixtures("clean_jobs")
def test_command_backgrounded_exception():
    """Verify CommandBackgrounded carries its job_pid attribute."""

    exc = CommandBackgrounded(42)
    assert exc.job_pid == 42


@pytest.mark.usefixtures("clean_jobs")
def test_command_cancelled_exception():
    """Verify CommandCancelled carries its job_pid attribute."""

    exc = CommandCancelled(99)
    assert exc.job_pid == 99


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_stop_dont_delete():
    """Verify that stop(dont_delete=True) cancels the task but leaves the job in the registry."""

    i_was_started = False

    @recline.command(name="test")
    async def test_coro():
        nonlocal i_was_started
        try:
            while True:
                i_was_started = True
                await asyncio.sleep(0.001)
        except asyncio.CancelledError:
            pass

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    job_pid = thread.job_pid
    thread.start()
    while not i_was_started:
        pass
    thread.stop(dont_delete=True)
    while thread.is_alive():
        pass
    # Job should still be registered because dont_delete=True
    assert job_pid in recline.JOBS


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_foreground_killed():
    """Verify that foreground() raises CommandCancelled when the thread was killed."""

    i_was_started = False

    @recline.command(name="test")
    async def test_coro():
        nonlocal i_was_started
        try:
            while True:
                i_was_started = True
                await asyncio.sleep(0.001)
        except asyncio.CancelledError:
            pass

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    thread.start()
    while not i_was_started:
        pass
    thread.stop()
    while thread.is_alive():
        pass
    with pytest.raises(CommandCancelled):
        thread.foreground()


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_foreground_backgrounded():
    """Verify that foreground() raises CommandBackgrounded when the thread is moved
    to the background while foreground() is waiting.
    """

    ready = [False]

    @recline.command(name="test")
    async def test_coro():
        while True:
            ready[0] = True
            await asyncio.sleep(0.001)

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    thread.start()
    while not ready[0]:
        pass

    # Trigger background() from a separate thread after a short delay
    def do_background():
        time.sleep(0.05)
        thread.background()

    t = threading.Thread(target=do_background)
    t.start()

    with pytest.raises(CommandBackgrounded):
        thread.foreground()

    t.join()
    # Remove the job from the registry so it doesn't pollute subsequent tests
    recline.JOBS.pop(thread.job_pid, None)
    thread._loop.call_soon_threadsafe(thread._task.cancel)


def test_set_terminal_echo_no_termios(monkeypatch):
    """Verify set_terminal_echo gracefully yields when termios is unavailable (e.g. Windows)."""

    # Setting termios to None in sys.modules causes 'import termios' to raise ImportError
    monkeypatch.setitem(sys.modules, "termios", None)

    ran = [False]
    with set_terminal_echo(enabled=False):
        ran[0] = True
    assert ran[0]


def test_set_terminal_echo_with_tty(monkeypatch):
    """Verify set_terminal_echo modifies echo when stdin is a real TTY."""

    fake_attrs = [0, 0, 0, termios.ECHO, 0, 0, [b'\x00'] * 19]
    set_calls = []

    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    monkeypatch.setattr(os, "isatty", lambda fd: True)
    monkeypatch.setattr(termios, "tcgetattr", lambda fd: list(fake_attrs))
    monkeypatch.setattr(termios, "tcsetattr", lambda fd, when, attrs: set_calls.append(attrs))

    with set_terminal_echo(enabled=False):
        pass

    # set_attr called twice: once to disable ECHO, once in finally to restore
    assert len(set_calls) == 2


def test_set_terminal_echo_enabled_true(monkeypatch):
    """Verify set_terminal_echo correctly enables ECHO (covering the enabled=True branch)."""

    # Start with ECHO disabled (bit not set)
    fake_attrs = [0, 0, 0, 0, 0, 0, [b'\x00'] * 19]
    set_calls = []

    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    monkeypatch.setattr(os, "isatty", lambda fd: True)
    monkeypatch.setattr(termios, "tcgetattr", lambda fd: list(fake_attrs))
    monkeypatch.setattr(termios, "tcsetattr", lambda fd, when, attrs: set_calls.append(attrs))

    with set_terminal_echo(enabled=True):
        pass

    assert len(set_calls) == 2


def test_set_terminal_echo_non_tty(monkeypatch):
    """Verify set_terminal_echo yields without changes when stdin is not a TTY."""

    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    monkeypatch.setattr(os, "isatty", lambda fd: False)

    ran = [False]
    with set_terminal_echo(enabled=False):
        ran[0] = True
    assert ran[0]
