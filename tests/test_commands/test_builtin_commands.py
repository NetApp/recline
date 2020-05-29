"""
Copyright (C) 2019 NetApp Inc.
All rights reserved.

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
