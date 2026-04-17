"""
Original © NetApp 2024

A test module for the recline.commands.builtin_commands module
"""

import pdb
import pudb
import pytest

import recline
from recline.commands import builtin_commands
from recline.commands.cli_command import CLICommand


@pytest.mark.parametrize("commands, expected_commands, expected_groups", [
    (
        [{"name": "command1", "group": "group1", "is_alias": False, "hidden": False}],
        ["command1"],
        ["group1"],
    ),
    (
        [{"name": "command1", "group": "group1", "is_alias": False, "hidden": True}],
        [],
        [],
    ),
    (
        [
            {"name": "command1", "group": "group1", "is_alias": False, "hidden": False},
            {"name": "c1", "group": "group1", "is_alias": True, "hidden": False},
        ],
        ["command1"],
        ["group1"],
    ),
    (
        [
            {"name": "command1", "group": "group1", "is_alias": False, "hidden": False},
            {"name": "command2", "group": "group2", "is_alias": False, "hidden": False},
            {"name": "command3", "group": "group1", "is_alias": True, "hidden": False},
            {"name": "command4", "group": "group2", "is_alias": False, "hidden": True},
        ],
        ["command1", "command2"],
        ["group1", "group2"],
    ),
    (
        [
            {
                "name": "builtincommand",
                "group": builtin_commands._GROUPNAME,
                "is_alias": False, "hidden": False,
            },
            {"name": "othercommand", "group": "group1", "is_alias": False, "hidden": False},
            {"name": "othercommand2", "group": "group1", "is_alias": False, "hidden": True},
        ],
        ["builtincommand", "othercommand"],
        [builtin_commands._GROUPNAME, "group1"],
    ),
])
def test_help_command(commands, expected_commands, expected_groups, capsys):
    """Verify that the help command prints out all of the available commands and
    none of their aliases or hidden commands.
    """

    for command in commands:
        recline.commands.COMMAND_REGISTRY[command["name"]] = CLICommand(lambda: None, **command)

    builtin_commands.command_help()
    captured = capsys.readouterr()
    for command in expected_commands:
        assert command in captured.out
    for group in expected_groups:
        assert group in captured.out

    for command in commands:
        if command["name"] not in expected_commands:
            assert command["name"] not in captured.out
        if command["group"] not in expected_groups:
            assert command["group"] not in captured.out


def test_exit_command():
    """Verify we exit the application"""

    with pytest.raises(SystemExit):
        builtin_commands.exit_command()


@pytest.mark.parametrize('use_pudb', [True, False])
def test_debug_command(use_pudb, monkeypatch, capsys):
    """Verify that we try to set a trace point"""

    set_a_trace = False

    def mock_set_trace():
        nonlocal set_a_trace
        set_a_trace = True

    def raise_set_trace():
        raise ImportError('Non-existent for UT pretend')

    if use_pudb:
        monkeypatch.setattr(pudb, 'set_trace', mock_set_trace)
    else:
        monkeypatch.setattr(pudb, 'set_trace', raise_set_trace)
    monkeypatch.setattr(pdb, 'set_trace', mock_set_trace)

    builtin_commands.debug()
    assert set_a_trace
    captured = capsys.readouterr()
    assert 'break back to the debugger' in captured.out


def test_man_commands_returns_non_aliases():
    """Verify man_commands() returns only non-alias command names."""

    recline.commands.COMMAND_REGISTRY["real_cmd"] = CLICommand(lambda: None, name="real_cmd", is_alias=False)
    recline.commands.COMMAND_REGISTRY["alias_cmd"] = CLICommand(lambda: None, name="alias_cmd", is_alias=True)

    result = builtin_commands.man_commands()
    assert "real_cmd" in result
    assert "alias_cmd" not in result


def test_exit_command_with_jobs_decline(monkeypatch):
    """Verify exit_command() with backgrounded jobs does NOT exit if user declines."""

    import recline

    monkeypatch.setattr(recline, "JOBS", {1: object()})
    monkeypatch.setattr("builtins.input", lambda _: "n")
    # Should return without raising SystemExit
    builtin_commands.exit_command()


def test_exit_command_with_jobs_accept(monkeypatch):
    """Verify exit_command() with backgrounded jobs exits when user confirms."""

    import recline

    class _FakeJob:
        def stop(self, dont_delete=False):
            pass

    monkeypatch.setattr(recline, "JOBS", {1: _FakeJob()})
    monkeypatch.setattr("builtins.input", lambda _: "yes")

    with pytest.raises(SystemExit):
        builtin_commands.exit_command()


def test_exit_command_abort_jobs(monkeypatch):
    """Verify exit_command() with abort_jobs=True cleans up jobs and exits."""

    import recline

    stopped = []

    class _FakeJob:
        def stop(self, dont_delete=False):
            stopped.append(dont_delete)

    monkeypatch.setattr(recline, "JOBS", {1: _FakeJob()})
    with pytest.raises(SystemExit):
        builtin_commands.exit_command(abort_jobs=True)
    assert stopped == [True]


def test_fg_no_jobs(monkeypatch):
    """Verify fg() raises ReclineCommandError when there are no jobs."""

    import recline
    from recline.commands import ReclineCommandError

    monkeypatch.setattr(recline, "JOBS", {})
    with pytest.raises(ReclineCommandError, match="No running jobs"):
        builtin_commands.fg()


def test_fg_invalid_job(monkeypatch):
    """Verify fg() raises ReclineCommandError for an unknown job ID."""

    import recline
    from recline.commands import ReclineCommandError

    monkeypatch.setattr(recline, "JOBS", {1: object()})
    with pytest.raises(ReclineCommandError, match="Could not find"):
        builtin_commands.fg(job=999)


def test_fg_with_job_no_formatter(monkeypatch):
    """Verify fg() completes silently when the job's command has no output formatter."""

    import recline

    class _FakeCommand:
        output_formatter = None

    class _FakeThread:
        command = _FakeCommand()

        def foreground(self):
            return 42

    monkeypatch.setattr(recline, "JOBS", {1: _FakeThread()})
    # Should not raise and should not print anything
    builtin_commands.fg(job=1)


def test_help_command_skips_alias_builtin(capsys):
    """Verify the 'continue' branch in command_help() is hit for alias/hidden builtins."""

    recline.commands.COMMAND_REGISTRY["real_builtin"] = CLICommand(
        lambda: None, name="real_builtin",
        group=builtin_commands._GROUPNAME,
        is_alias=False, hidden=False,
    )
    recline.commands.COMMAND_REGISTRY["alias_builtin"] = CLICommand(
        lambda: None, name="alias_builtin",
        group=builtin_commands._GROUPNAME,
        is_alias=True, hidden=False,
    )

    builtin_commands.command_help()
    captured = capsys.readouterr()
    assert "real_builtin" in captured.out
    assert "alias_builtin" not in captured.out


def test_debug_interrupt_handler_callable(monkeypatch):
    """Verify that no_native_int_support (assigned to pudb.set_interrupt_handler) is callable."""

    original_handler = pudb.set_interrupt_handler
    monkeypatch.setattr(pudb, "set_interrupt_handler", original_handler)
    monkeypatch.setattr(pudb, "set_trace", lambda: None)

    builtin_commands.debug()
    # After debug(), pudb.set_interrupt_handler is no_native_int_support; call it to cover pass
    pudb.set_interrupt_handler()


def test_fg_with_valid_job(monkeypatch):
    """Verify fg() calls foreground() and formats output for a known job."""

    import recline

    formatted = []

    class _FakeFormatter:
        def format_output(self, val):
            formatted.append(val)

    class _FakeCommand:
        output_formatter = _FakeFormatter()

    class _FakeThread:
        command = _FakeCommand()

        def foreground(self):
            return 42

    monkeypatch.setattr(recline, "JOBS", {1: _FakeThread()})
    builtin_commands.fg(job=1)
    assert formatted == [42]


def test_man_unknown_command(capsys):
    """Verify man() prints a 'No manual entry' note for unknown commands."""

    builtin_commands.man(["nonexistent", "cmd"])
    captured = capsys.readouterr()
    assert "No manual entry for" in captured.out


def test_man_command_large_window(monkeypatch):
    """Test man command with a large window so all text fits and (END) is displayed."""

    import curses

    @recline.command(name="man large cmd")
    def _man_large():
        """Short description for large-window man test."""

    class _LargeWindow:
        def __init__(self):
            self.rows = 100
            self.cols = 80
            self._y = 0
            self._keys = iter([curses.KEY_DOWN, ord('q')])

        def getmaxyx(self): return self.rows, self.cols
        def getyx(self): return self._y, 0
        def clear(self): self._y = 0
        def refresh(self): pass

        def addstr(self, *args):
            text = ""
            if len(args) >= 3 and isinstance(args[0], int):
                text = args[2] if isinstance(args[2], str) else ""
            elif args and isinstance(args[0], str):
                text = args[0]
            self._y = min(self._y + text.count('\n'), self.rows - 1)

        def getch(self):
            return next(self._keys, ord('q'))

    monkeypatch.setattr(curses, "wrapper", lambda fn: fn(_LargeWindow()))
    monkeypatch.setattr(curses, "curs_set", lambda n: None)

    recline.PROGRAM_NAME = "test_prog"
    builtin_commands.man(["man", "large", "cmd"])


def test_man_command_scrolling(monkeypatch):
    """Test man command with a small window to exercise KEY_DOWN and KEY_UP scrolling."""

    import curses

    @recline.command(name="man scroll cmd")
    def _man_scroll():
        """Short desc for scroll test.

        Longer description that adds more content to the man page for scrolling.
        """

    class _SmallWindow:
        def __init__(self):
            self.rows = 4
            self.cols = 80
            self._y = 0
            self._keys = iter([
                curses.KEY_DOWN, curses.KEY_DOWN,
                curses.KEY_UP, curses.KEY_UP,
                ord('q'),
            ])

        def getmaxyx(self): return self.rows, self.cols
        def getyx(self): return self._y, 0
        def clear(self): self._y = 0
        def refresh(self): pass

        def addstr(self, *args):
            text = ""
            if len(args) >= 3 and isinstance(args[0], int):
                text = args[2] if isinstance(args[2], str) else ""
            elif args and isinstance(args[0], str):
                text = args[0]
            self._y = min(self._y + text.count('\n'), self.rows - 1)

        def getch(self):
            return next(self._keys, ord('q'))

    monkeypatch.setattr(curses, "wrapper", lambda fn: fn(_SmallWindow()))
    monkeypatch.setattr(curses, "curs_set", lambda n: None)

    recline.PROGRAM_NAME = "test_prog"
    builtin_commands.man(["man", "scroll", "cmd"])
