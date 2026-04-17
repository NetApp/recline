"""
Original © NetApp 2024

A test module for the recline.repl.shell module
"""

import asyncio
import builtins

import pytest

import recline
from recline.repl import shell


@pytest.mark.parametrize("user_input, expected_marker, expected_output", [
    ("ut command -arg 2", 2, ""),
    ("ut command", None, "required: -arg"),
    ("ut command -arg 5", None, "This is a UT failure"),
    ("ut command -arg foo", None, "invalid int value"),
    ("bad command", None, "Unknown command"),
    ("ut command -arg 2 && ut command -arg 3", 3, ""),
    ("ut command; ut command -arg 3", 3, "required: -arg"),
    ("ut command -arg 5 && ut command -arg 2", None, "This is a UT failure"),
    ("ut command -arg 2 || ut command -arg 1", 2, ""),
    ("bad command; bad other command || ut command -arg 3", 3, "Unknown command"),
])
def test_shell_execute(user_input, expected_marker, expected_output, capsys):
    """Test that our shell can run one or more commands on input"""

    ut_marker = None

    @recline.command(name="ut command")
    def ut_command(arg: int):
        if arg == 5:
            raise ValueError("This is a UT failure")
        nonlocal ut_marker
        ut_marker = arg

    shell.execute(user_input)
    assert ut_marker == expected_marker
    captured = capsys.readouterr()
    assert expected_output in captured.out + captured.err


@pytest.mark.parametrize("user_input, expected_marker", [
    ("ut async command -arg 2", 2), ("ut async command -arg 30", 30),
])
def test_shell_execute_async_command(user_input, expected_marker):
    """Verify we can run async commands as well"""

    ut_marker = None

    @recline.command(name="ut async command")
    async def ut_command(arg: int):
        loops = 0
        while loops < arg:
            loops += 1
            await asyncio.sleep(0.001)
        nonlocal ut_marker
        ut_marker = arg

    shell.execute(user_input)
    assert ut_marker == expected_marker


def test_run_startup_exit_command(monkeypatch):
    """Verify that a command which is marked to run at startup or exit gets run"""

    startup_command_ran = False
    recline.commands.START_COMMAND = None

    def mock_eof(prompt):
        raise EOFError("UT is finished")

    monkeypatch.setattr(builtins, "input", mock_eof)

    @recline.command(atstart=True)
    def startup():
        nonlocal startup_command_ran
        startup_command_ran = True

    with pytest.raises(SystemExit):
        shell.relax(argv=["ut_program"])

    assert startup_command_ran
    recline.commands.START_COMMAND = None


@pytest.mark.parametrize("motd, expected", [
    ("This is a simple message", "This is a simple message"),
    (lambda: "This is a dynamic message", "This is a dynamic message"),
])
def test_run_motd(motd, expected, monkeypatch, capsys):
    """Verify the MOTD gets printed if one is provided"""

    def mock_eof(prompt):
        raise EOFError("UT is finished")

    monkeypatch.setattr(builtins, "input", mock_eof)
    with pytest.raises(SystemExit):
        shell.relax(argv=["ut_program"], motd=motd)

    captured = capsys.readouterr()
    assert expected in captured.out


def test_run_with_dash_c():
    """Verify only a single command is run when -c is passed in"""

    command_name = "single command dash c"
    preexisting = command_name in recline.commands.COMMAND_REGISTRY

    @recline.command(name=command_name)
    def single_cmd():
        return 73

    try:
        assert shell.relax(argv=["ut_program", "-c", "single", "command", "dash", "c"]) == 73
        assert command_name in recline.commands.COMMAND_REGISTRY
    finally:
        if not preexisting:
            recline.commands.COMMAND_REGISTRY.pop(command_name, None)

    if not preexisting:
        assert command_name not in recline.commands.COMMAND_REGISTRY


def test_run_non_repl():
    """Verify that if a program is not trying to be a repl, then we will parse
    a command from the input and exit
    """

    @recline.command(name="single command non repl")
    def single_cmd():
        return 73

    assert shell.relax(argv=["ut_program", "single", "command", "non", "repl"], repl_mode=False) == 73


def test_run_single_command():
    """Verify that if a program is not trying to be a repl, then we will parse
    a command from the input and exit
    """

    @recline.command(name="single command one shot")
    def single_cmd_one_shot():
        return 73

    assert shell.relax(argv=["ut_program"], single_command="single command one shot") == 73


def test_relax_uses_sys_argv_when_none(monkeypatch):
    """Verify that relax() uses sys.argv when no argv is provided (covers the argv=None branch)."""

    import sys

    @recline.command(name="single command sys argv")
    def single_cmd():
        return 45

    monkeypatch.setattr(sys, "argv", ["ut_program", "-c", "single", "command", "sys", "argv"])
    result = shell.relax()
    assert result == 45


def test_relax_repl_loop_empty_input(monkeypatch):
    """Verify that entering an empty string in the REPL loop is silently skipped."""

    import builtins

    calls = [0]

    def mock_input(prompt):
        calls[0] += 1
        if calls[0] == 1:
            return ""  # empty → should continue
        raise EOFError

    monkeypatch.setattr(builtins, "input", mock_input)
    with pytest.raises(SystemExit):
        shell.relax(argv=["ut_program"])
    assert calls[0] == 2  # was called twice


def test_relax_repl_loop_executes_command(monkeypatch):
    """Verify that a valid command entered in the REPL loop gets executed."""

    import builtins

    ran = [False]
    calls = [0]

    @recline.command(name="loop test command")
    def loop_test():
        ran[0] = True

    def mock_input(prompt):
        calls[0] += 1
        if calls[0] == 1:
            return "loop test command"
        raise EOFError

    monkeypatch.setattr(builtins, "input", mock_input)
    with pytest.raises(SystemExit):
        shell.relax(argv=["ut_program"])
    assert ran[0]


def test_relax_repl_loop_keyboard_interrupt(monkeypatch, capsys):
    """Verify that KeyboardInterrupt in the REPL loop prints ^C and continues."""

    import builtins

    calls = [0]

    def mock_input(prompt):
        calls[0] += 1
        if calls[0] == 1:
            raise KeyboardInterrupt
        raise EOFError

    monkeypatch.setattr(builtins, "input", mock_input)
    with pytest.raises(SystemExit):
        shell.relax(argv=["ut_program"])

    captured = capsys.readouterr()
    assert "^C" in captured.out


def test_relax_repl_loop_debug_interrupt(monkeypatch, capsys):
    """Verify that DebugInterrupt is caught and debug() is invoked."""

    import builtins
    from recline.commands import builtin_commands as bc

    debug_called = [False]
    calls = [0]

    def mock_input(prompt):
        calls[0] += 1
        if calls[0] == 1:
            return "debug trigger"  # command that will raise DebugInterrupt via mock execute
        raise EOFError

    def mock_execute(cmd):
        raise bc.DebugInterrupt()

    def mock_debug():
        debug_called[0] = True

    monkeypatch.setattr(builtins, "input", mock_input)
    monkeypatch.setattr(shell, "execute", mock_execute)
    monkeypatch.setattr(bc, "debug", mock_debug)

    with pytest.raises(SystemExit):
        shell.relax(argv=["ut_program"])

    assert debug_called[0]


def test_split_unquoted_escaped_separator():
    """Verify that _split_unquoted treats a backslash-escaped separator as literal."""

    from recline.repl.shell import _split_unquoted

    # The \; should NOT be treated as a separator
    result = _split_unquoted("a \\; b", ";")
    assert result == ["a \\; b"]


def test_split_unquoted_single_quoted_separator():
    """Verify that _split_unquoted ignores separators inside single quotes."""

    from recline.repl.shell import _split_unquoted

    result = _split_unquoted("a ';' b", ";")
    assert result == ["a ';' b"]


def test_split_unquoted_double_quoted_separator():
    """Verify that _split_unquoted ignores separators inside double quotes."""

    from recline.repl.shell import _split_unquoted

    result = _split_unquoted('a ";" b', ";")
    assert result == ['a ";" b']


def test_execute_or_chain_all_fail(capsys):
    """Verify that the || chain iterates to completion when all commands fail."""

    result = shell.execute("bad cmd1 || bad cmd2")
    assert result == 1
    captured = capsys.readouterr()
    assert "Unknown command" in captured.out


def test_run_one_command_question_mark_becomes_help(capsys):
    """Verify that a trailing ? in a command is converted to -help."""

    @recline.command(name="ut help command")
    def ut_help_command(arg: int):
        """A command for testing help substitution"""

    # '?' should trigger the help output and cause a non-fatal SystemExit
    result = shell.run_one_command("ut help command ?")
    # argparse help exits with code 0, run_one_command returns that exit code
    assert result == 0


def test_run_one_command_with_output_formatter(capsys):
    """Verify that when a command has an output_formatter, it is called and 0 is returned."""

    from recline.formatters.output_formatter import OutputFormatter
    from typing import Annotated

    class _FmtFormatter(OutputFormatter):
        def format_output(self, results):
            print(f"formatted:{results}")

    @recline.command(name="fmt command")
    def fmt_command() -> Annotated[str, _FmtFormatter]:
        return "hello"

    result = shell.run_one_command("fmt command")
    assert result == 0
    captured = capsys.readouterr()
    assert "formatted:hello" in captured.out


def test_run_one_command_backgrounded(capsys):
    """Verify that CommandBackgrounded is caught and reports the job correctly."""

    import asyncio

    @recline.command(name="bg async command")
    async def bg_async():
        await asyncio.sleep(10)

    result = shell.run_one_command("bg async command -background")
    assert result == 0
    captured = capsys.readouterr()
    assert "running in the background" in captured.out
    # clean up the job
    recline.JOBS.clear()
    recline.NEXT_JOB_PID = 1


def test_run_one_command_recline_command_error(capsys):
    """Verify that ReclineCommandError from a command is reported and returns 1."""

    from recline.commands import ReclineCommandError

    @recline.command(name="err command")
    def err_command():
        raise ReclineCommandError("intended error")

    result = shell.run_one_command("err command")
    assert result == 1
    captured = capsys.readouterr()
    assert "intended error" in captured.out


def test_run_one_command_command_cancelled(monkeypatch):
    """Verify that CommandCancelled from a command is silently swallowed (returns 1)."""

    from recline.commands.async_command import CommandCancelled
    from recline.commands.cli_command import CLICommand

    monkeypatch.setitem(
        recline.commands.COMMAND_REGISTRY, "__cancel_test", CLICommand(lambda: None, name="__cancel_test")
    )

    def _raise_cancelled(cmd, args):
        raise CommandCancelled(99)

    monkeypatch.setattr(shell, "_run_command", _raise_cancelled)
    result = shell.run_one_command("__cancel_test")
    assert result == 1


def test_track_command_history_happy_path(monkeypatch):
    """Verify track_command_history reads history and sets length when file is readable."""

    import readline as _rl

    read_called = [False]
    length_set = [None]

    monkeypatch.setattr(_rl, "read_history_file", lambda f: read_called.__setitem__(0, True))
    monkeypatch.setattr(_rl, "set_history_length", lambda n: length_set.__setitem__(0, n))

    shell.track_command_history("/fake/path/history")
    assert read_called[0]
    assert length_set[0] == 1000


def test_run_one_command_reraises_exit_command_code():
    """Verify that a SystemExit with EXIT_COMMAND_CODE is re-raised."""

    import sys
    from recline.commands import builtin_commands as bc
    from recline.commands.cli_command import CLICommand

    def _do_exit():
        sys.exit(bc.EXIT_COMMAND_CODE)

    recline.commands.COMMAND_REGISTRY["__test_exit_code"] = CLICommand(_do_exit, name="__test_exit_code")

    with pytest.raises(SystemExit) as exc_info:
        shell.run_one_command("__test_exit_code")
    assert exc_info.value.code == bc.EXIT_COMMAND_CODE


def test_setup_repl_with_program_name_prompt_history(monkeypatch, tmp_path):
    """Verify that _setup_repl respects program_name, prompt, and history_file overrides."""

    import builtins

    history_file = str(tmp_path / "history.txt")

    def mock_eof(prompt):
        raise EOFError

    monkeypatch.setattr(builtins, "input", mock_eof)
    with pytest.raises(SystemExit):
        shell.relax(
            argv=["ut_program"],
            program_name="myapp",
            prompt="myapp> ",
            history_file=history_file,
        )
    assert recline.PROGRAM_NAME == "myapp"
    assert recline.PROMPT == "myapp> "


def test_setup_repl_registers_exit_command(monkeypatch):
    """Verify that an atexit command is registered in _setup_repl."""

    import builtins

    @recline.command(name="at exit cmd", atexit=True)
    def at_exit_cmd():
        pass

    def mock_eof(prompt):
        raise EOFError

    monkeypatch.setattr(builtins, "input", mock_eof)
    with pytest.raises(SystemExit):
        shell.relax(argv=["ut_program"])
    # atstart/atexit cleanup
    recline.commands.EXIT_COMMAND = None


def test_setup_repl_start_command_backgrounded(monkeypatch):
    """Verify that a start command that gets backgrounded is silently handled."""

    import asyncio
    import builtins

    @recline.command(name="bg startup", atstart=True, background=True)
    async def bg_startup():
        await asyncio.sleep(10)

    def mock_eof(prompt):
        raise EOFError

    monkeypatch.setattr(builtins, "input", mock_eof)
    # Should not raise - CommandBackgrounded from START_COMMAND should be caught
    with pytest.raises(SystemExit):
        shell.relax(argv=["ut_program"])
    recline.commands.START_COMMAND = None
    recline.JOBS.clear()
    recline.NEXT_JOB_PID = 1


def test_track_command_history_missing_file(tmp_path):
    """Verify that track_command_history silently handles a missing history file."""

    missing = str(tmp_path / "nonexistent" / "history.txt")
    # Should not raise
    shell.track_command_history(missing)


def test_track_command_history_existing_file(tmp_path):
    """Verify that track_command_history loads an existing history file successfully."""

    history_file = tmp_path / "history.txt"
    history_file.write_text("")
    # Should not raise
    shell.track_command_history(str(history_file))


def test_setup_tab_complete_gnu_readline(monkeypatch):
    """Verify setup_tab_complete works with GNU readline (no libedit in __doc__)."""

    import readline

    monkeypatch.setattr(readline, "__doc__", "GNU Readline library -- line editing support")
    # Should not raise
    shell.setup_tab_complete()
