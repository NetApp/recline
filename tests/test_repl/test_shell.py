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
    def ut_command(arg: int):  # pylint: disable=unused-variable
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
    async def ut_command(arg: int):  # pylint: disable=unused-variable
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
    def startup():  # pylint: disable=unused-variable
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

    @recline.command(name="single command")
    def single_command():  # pylint: disable=unused-variable
        return 73

    assert shell.relax(argv=["ut_program", "-c", "single", "command"]) == 73


def test_run_non_repl():
    """Verify that if a program is not trying to be a repl, then we will parse
    a command from the input and exit
    """

    @recline.command(name="single command")
    def single_command():  # pylint: disable=unused-variable
        return 73

    assert shell.relax(argv=["ut_program", "single", "command"], repl_mode=False) == 73


def test_run_single_command():
    """Verify that if a program is not trying to be a repl, then we will parse
    a command from the input and exit
    """

    @recline.command(name="single command")
    def single_command():  # pylint: disable=unused-variable
        return 73

    assert shell.relax(argv=["ut_program"], single_command="single command") == 73
