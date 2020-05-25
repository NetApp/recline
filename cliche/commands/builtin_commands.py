"""
The commands defined here are included with every cliche application
"""

from collections import OrderedDict
import curses
from operator import attrgetter
import sys

import cliche
from cliche.arg_types.flag import Flag
from cliche.arg_types.remainder import Remainder
from cliche.commands import ClicheCommandError
from cliche.commands.cli_command import command
from cliche.commands.man_utils import  generate_help_text


class DebugInterrupt(Exception):
    """An exception class to mark that we were interrupted by a debug request"""


EXIT_COMMAND_CODE = 222
_GROUPNAME = 'Built-in Commands'


@command(group=_GROUPNAME, aliases=['?'], name="help")
def command_help() -> None:
    """Display a list of available commands and their short description"""

    groups = OrderedDict()
    print('Available Commands:')
    print()
    for command_entry in cliche.commands.COMMAND_REGISTRY.values():
        if command_entry.is_alias or command_entry.hidden:
            continue

        command_group = command_entry.group if command_entry.group else ""
        if command_group not in groups:
            groups[command_group] = []
        groups[command_group].append(command_entry)

    # print the builtin functions last
    builtins = groups.pop(_GROUPNAME, [])

    for group in sorted(groups.keys()):
        if group:
            print('%s\n%s' % (group, '-' * len(group)))
        for command_entry in sorted(groups[group], key=attrgetter('name')):
            print('%s - %s' % (command_entry.name, command_entry.docstring.short_description))

    print()
    print('%s\n%s' % (_GROUPNAME, '-' * len(_GROUPNAME)))
    for command_entry in sorted(builtins, key=attrgetter('name')):
        if command_entry.is_alias or command_entry.hidden:
            continue
        print('%s - %s' % (command_entry.name, command_entry.docstring.short_description))


def man_commands(*_, **__):
    """A completer function for returning a list of commands the user might want
    to see the man page for. Don't show alias names to reduce clutter and confusion.
    """

    return [
        name for name, command in cliche.commands.COMMAND_REGISTRY.items() if not command.is_alias
    ]


@command(group=_GROUPNAME)
# pylint: disable=too-many-statements
def man(command_name: Remainder.define(completer=man_commands)) -> None:
    """Display the full man page for a given command

    Args:
        command: The name of the command
    """

    command_name = ' '.join(command_name)
    command_class = cliche.commands.COMMAND_REGISTRY.get(command_name, None)
    if not command_class:
        print('No manual entry for %s' % command_name)
        return

    def display_man(window):
        curses.curs_set(False)
        max_lines, max_cols = window.getmaxyx()
        help_text = generate_help_text(max_cols, command_class)
        window.clear()
        window.refresh()
        top = 0
        at_bottom = False
        at_top = True

        def _redraw_man_page():
            nonlocal at_bottom, at_top
            window.clear()

            # title
            window.addstr(0, 0, command_name)
            window.addstr(0, (max_cols - len(cliche.PROGRAM_NAME)) // 2, cliche.PROGRAM_NAME)
            window.addstr(0, max_cols - len(command_name), command_name)
            window.addstr('\n\n')

            index = top
            at_bottom = True
            at_top = top == 0
            while index < len(help_text):
                current_y, _ = window.getyx()
                room_left = max_lines - current_y - 1
                line = help_text[index]
                if '\n' not in line[0]:
                    window.addstr(*line)
                    index += 1
                    continue
                lines = line[0].split('\n')
                if len(lines) > room_left:
                    window.addstr('\n'.join(lines[:room_left]), *line[1:])
                    at_bottom = False
                    break
                window.addstr(*line)
                index += 1
            if at_bottom:
                window.addstr(max_lines - 1, 0, '(END)', curses.A_STANDOUT)

            window.refresh()

        # initial draw
        _redraw_man_page()

        # get key presses
        while True:
            key = window.getch()
            if key == ord('q'):
                break

            if key == curses.KEY_DOWN and not at_bottom:
                top += 1
                # if scrolling down and the "line" we just consumed isn't a full
                # line, then we need to keep going until we consume a \n
                while top < len(help_text) and not help_text[top - 1][0].endswith('\n'):
                    top += 1
            elif key == curses.KEY_UP and not at_top:
                top -= 1
                # if scrolling up and the "line" we're going to consume next time
                # isn't a full line, then we need to move the pointer until it is
                while top > 0 and not help_text[top - 1][0].endswith('\n'):
                    top -= 1

            _redraw_man_page()

    curses.wrapper(display_man)


@command(group=_GROUPNAME, aliases=['quit', 'q'], name="exit")
def exit_command(abort_jobs: Flag = False) -> None:
    """Exit the application"""

    if not abort_jobs and cliche.JOBS:
        answer = input("There are backgrounded jobs. Are you sure you want to quit? ")
        if answer.lower().startswith("y"):
            abort_jobs = True
        else:
            return

    if abort_jobs:
        # clean up the jobs before we call sys.exit. This prevents an issue where
        # a traceback is printed due to some cleanup code in async tasks:
        # > q -abort-jobs
        # Exception ignored in: <object repr() failed>
        # Traceback (most recent call last):
        # File "/usr/software/pkgs/Python-3.5.2/lib/python3.5/asyncio/tasks.py", line 85, in __del__
        # AttributeError: 'NoneType' object has no attribute '_PENDING'
        for job in cliche.JOBS.values():
            job.stop(dont_delete=True)
        cliche.JOBS = {}

    # now we should be safe to exit
    sys.exit(EXIT_COMMAND_CODE)


@command(group=_GROUPNAME, hidden=True)
def debug() -> None:
    """Drop into the Python debugger for development purposes"""

    try:
        import pudb  # pylint: disable=import-outside-toplevel
        # avoid pudb printing out an ugly message
        def no_native_int_support(*_x, **_y):
            pass

        pudb.set_interrupt_handler = no_native_int_support

        # the program pauses after this line
        pudb.set_trace()
    except ImportError:
        import pdb  # pylint: disable=import-outside-toplevel
        pdb.set_trace()
    finally:
        # remind the user that they can pause the program at any time
        print(r'Press ctrl+\ to break back to the debugger')


@command(group=_GROUPNAME)
def fg(job: int = None) -> None:  # pylint: disable=invalid-name
    """Bring a job to the foreground

    If the job has already completed, then its results will be printed to the
    console. If the job has not yet finished, then the application will wait for
    it to finish before printing the results.

    Args:
        job: The identifier of the job to track. If not provided, then the most
            recent job will be tracked.
    """

    if not job:
        try:
            job = sorted(cliche.JOBS.keys())[-1]
        except IndexError:
            raise ClicheCommandError("No running jobs found")
    elif job not in cliche.JOBS:
        raise ClicheCommandError("Could not find a running job for %s" % job)

    thread = cliche.JOBS[job]
    result = thread.foreground()
    if thread.command.output_formatter:
        thread.command.output_formatter.format_output(result)
