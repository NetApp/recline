"""
Original © NetApp 2024

This is the main staring point for a recline application
"""

import atexit
import os
import readline
import shlex
import signal
import sys
import traceback
from typing import Callable, List, Union

import recline
from recline import commands
from recline.arg_types.recline_type_error import ReclineTypeError
from recline.commands import ReclineCommandError, builtin_commands
from recline.commands.async_command import AsyncCommand, CommandBackgrounded, CommandCancelled
from recline.repl import completer


# pylint: disable=too-many-arguments,bad-continuation
def relax(
    argv: str = None,
    program_name: str = None,
    motd: Union[Callable[[], str], str] = None,
    history_file: str = None,
    prompt: str = None,
    repl_mode: bool = True,
    single_command: str = None,
) -> None:
    """This is the main entry point of a recline-based application. Call this after
    all of your commands have been defined.

    This will start the application in its REPL mode (by default) or in a single
    command mode if the first argv to is set to '-c'. If in REPL mode, this function
    will not return until the user quits the application.

    Args:
        argv: This is a list of arguments that usually comes from the command line.
            This will default to sys.argv[1:] but may be overridden if needed.
        program_name: If provided, this will be the name of the program (used
            internally for display purposes). If not provided, sys.argv[0] will
            be used as a default (the name of the script file, e.g. hello.py).
        motd: If provided, this will be displayed to the user before the prompt.
            If it is a string, it will be displayed as given. If it is a callable,
            then the result will be displayed to the user.
        history_file: If persistent command history is desired, a file name may
            be passed where a list of the most recent commands will be kept and
            loaded from.
        prompt: This is the prompt to display to the user to let them know that
            the system is ready to accept a command. If not provided, a default
            will be used.
        repl_mode: By default, applications using recline expect to act as a REPL
            environment where the user will run many commands. These applications
            can still run a single command if the user passes a -c. But, it is
            convienent for some applications to act more like a traditional CLI
            command without needing to pass -c. For those applicatinos, repl_mode
            can be set to False.
        single_command: This acts a bit like non-repl mode, except in this case
            the user doesn't have to pass any command name as an argument to the
            application, but rather whatever command name is passed here is automatically
            run and the application exits when the command is complete. If an
            application only had one command, such as an implementation of ls in
            Python, then this would be a good choice for exposing that command easily.
    """

    if argv is None:
        argv = sys.argv[:]

    _setup_repl(program_name, prompt, history_file, argv)

    if single_command or not repl_mode or argv and len(argv) >= 2 and argv[1] == "-c":
        # Some external process sent us a command to run (like scp or ssh or
        # so run it and exit
        command = argv[2:]
        if not repl_mode:
            command = argv[1:]
        if single_command:
            command = [single_command] + argv[1:]
        return run_one_command(f"{' '.join(command)}")

    if isinstance(motd, str):
        print(motd)
    elif motd:
        print(motd())

    # The main loop (the L in REPL)
    while True:
        try:
            current_input = input(recline.PROMPT).strip()  # the R in REPL
            if current_input == "":
                continue
            execute(current_input)  # The E and P in REPL
        except (KeyboardInterrupt, CommandCancelled):
            # This is what bash looks like if you interrupt it. It will print out
            # the ^C character and go to the next line.
            sys.stdout.write("^C\n")
        except builtin_commands.DebugInterrupt:
            # This makes it look less confusing after returning from a debug break
            # otherwise the prompt isn't seen unless the user presses enter
            sys.stdout.write("\n")
            builtin_commands.debug()
        except EOFError:
            # If the terminal is closed on us (maybe SSH exit), just exit the app
            sys.exit(0)


def execute(current_input: str) -> int:
    """Execute the input as a series of commands"""

    result = 0

    if ';' in current_input:
        for command in current_input.split(';'):
            result = execute(command)
        return result

    if '&&' in current_input:
        for command in current_input.split('&&'):
            result = execute(command)
            if result > 0:
                break
        return result

    if "||" in current_input:
        for command in current_input.split('||'):
            result = execute(command)
            if result == 0:
                break
        return result

    # if it is a simple command, run it
    return run_one_command(current_input.strip())


def run_one_command(current_input: str) -> int:
    """ Parse the current input, search for a matching command and execute it
        with the given parameters.
    """

    command_name = completer.CommandCompleter.get_command_name(
        current_input, list(commands.COMMAND_REGISTRY.keys()),
    )
    if command_name not in commands.COMMAND_REGISTRY:
        print(f"Unknown command: {current_input}")
        return 1
    command = commands.COMMAND_REGISTRY[command_name]
    cmd_args = [f for f in shlex.split(current_input.replace(command_name, "", 1)) if f]
    if cmd_args and cmd_args[-1] == "?" and command_name != "?":
        cmd_args[-1] = "-help"
    try:
        result = _run_command(command, cmd_args)
        if command.output_formatter:
            command.output_formatter.format_output(result)
            # the command ran to completion without exception so we'll say the
            # return code is 0
            return 0
        return result
    except CommandBackgrounded as err:
        print(f'^Z\nJob {err.job_pid} is running in the background')
        return 0
    except CommandCancelled:
        pass
    except (ReclineTypeError, ReclineCommandError) as exc:
        print(str(exc))
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Command execution error: {exc}")
        traceback.print_exc()
    except SystemExit as exc:
        if exc.code == builtin_commands.EXIT_COMMAND_CODE:
            raise

        # if a command fails to parse, that's OK. The user probably just didn't
        # type one of the required parameters yet. We might also get here if they
        # printed the help output with -help
        return exc.code
    return 1


def _setup_repl(program_name: str, prompt: str, history_file: str, argv: List[str]) -> None:
    if not program_name:
        recline.PROGRAM_NAME = argv[0].split(os.path.sep)[-1]
    else:
        recline.PROGRAM_NAME = program_name

    if prompt is not None:
        recline.PROMPT = prompt

    if history_file:
        track_command_history(history_file)
    setup_tab_complete()

    if sys.platform != "win32":
        # set up a handler for ctrl-\
        def signal_handler(signum, frame):
            raise builtin_commands.DebugInterrupt()
        signal.signal(signal.SIGQUIT, signal_handler)

    if commands.EXIT_COMMAND:
        atexit.register(_run_command, commands.EXIT_COMMAND, [])

    if commands.START_COMMAND:
        try:
            _run_command(commands.START_COMMAND, argv[1:])
        except CommandBackgrounded:
            pass


def _run_command(command: str, cmd_args: List[str]) -> int:
    namespace = command.parser.parse_args(args=cmd_args)

    args = [getattr(namespace, arg.name) for arg in command.required_args]
    kwargs = {
        arg.name: getattr(namespace, arg.name)
        for arg in command.optional_args if hasattr(namespace, arg.name)
    }

    result = None
    if command.is_async:
        command_thread = AsyncCommand(command, *args, **kwargs)
        command_thread.start()
        if namespace.background or command.is_background:
            raise CommandBackgrounded(command_thread.job_pid)
        result = command_thread.foreground()
    else:
        result = command.func(*args, **kwargs)
    if result is None:
        result = 0
    return result


def track_command_history(filename: str) -> None:
    """load/save command history"""

    try:
        readline.read_history_file(filename)
        # default history len is -1 (infinite), which may grow unruly
        readline.set_history_length(1000)
    except IOError:
        pass
    atexit.register(readline.write_history_file, filename)


def setup_tab_complete() -> None:
    """Set up the readline library to hook into our command completer"""

    readline.set_completer_delims("")
    if sys.platform == "linux":
        # pyreadline3 (used for windows) doesn't implement this
        # libedit (default for macos) implements this but never calls it (broken)
        readline.set_completion_display_matches_hook(completer.match_command_hook)
    readline.set_completer(completer.CommandCompleter(commands.COMMAND_REGISTRY).completer)
    if readline.__doc__ and "libedit" in readline.__doc__:
        # macos doesn't use GNU readline, but BSD libedit instead
        readline.parse_and_bind("bind '\t' rl_complete")
        readline.parse_and_bind("bind '^R' em-inc-search-prev")
    else:
        readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set show-all-if-ambiguous on")
    readline.parse_and_bind("set bell-style none")
