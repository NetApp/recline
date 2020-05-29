"""
Copyright (C) 2019 NetApp Inc.
All rights reserved.

A test module for the recline.repl.completer module
"""

import pytest

import recline
from recline.commands.cli_command import command
from recline.repl.completer import CommandCompleter, match_command_hook


@pytest.mark.parametrize("prompt, current_input, matches, expected_output", [
    (
        "> ", "input", [],
        "\n\n> \r> ",
    ),
    (
        ">>> ", "part", ["part of", "partial"],
        "\npart of  partial  \n>>> \r>>> ",
    ),
    (
        "> ", "p", ["part of", "partial", "partner", "pool", "pony"],
        "\npart of  partial  partner  \npool     pony     \n> \r> ",
    ),
])
# pylint: disable=too-many-arguments
def test_match_command_hook(prompt, current_input, matches, expected_output, monkeypatch, capsys):
    """Verify our match hook for readline's set_completion_display_matches_hook()
    prints out the right output
    """

    monkeypatch.setattr(recline, "PROMPT", prompt)
    match_command_hook(current_input, matches)
    captured = capsys.readouterr()
    assert captured.out == expected_output


@pytest.mark.parametrize("partial, possibles, exact, match", [
    ("cake show -cake 1", ["cake show", "cake make", "cake make again"], False, "cake show"),
    ("cake make", ["cake show", "cake make", "cake make again"], False, None),
    ("cake make", ["cake show", "cake make", "cake make again"], True, "cake make"),
    ("help", ["cake show", "cake make", "cake make again"], True, None),
])
def test_command_completer_get_command_name(partial, possibles, exact, match):
    """Verify we can complete a command name given a partial and a list of possibles
    where only one possible matches the partial.
    """

    assert CommandCompleter.get_command_name(partial, possibles, exact=exact) == match


@pytest.mark.parametrize("partial, index, commands, expected_output", [
    ("", 0, ["cake show", "cake make", "cake make again", "cake eat"], "cake eat "),
    ("cak", 0, ["cake show", "cake make", "cake make again", "cake eat"], "cake eat "),
    ("cak", 1, ["cake show", "cake make", "cake make again", "cake eat"], "cake make "),
    ("cak", 2, ["cake show", "cake make", "cake make again", "cake eat"], "cake make again "),
    ("cak", 3, ["cake show", "cake make", "cake make again", "cake eat"], "cake show "),
    ("cake show", 0, ["cake show", "cake make", "cake make again", "cake eat"], "cake show "),
    ("cake show ", 0, ["cake show", "cake make", "cake eat"], "cake show -arg "),
    ("cake show -a", 0, ["cake show", "cake make", "cake eat"], "cake show -arg "),
    ("cake show -arg 1 ", 0, ["cake show", "cake make", "cake eat"], None),
    ("cak", 0, ["cake", "cake show"], "cake "),
    ("cak", 1, ["cake", "cake show"], "cake show "),
    ("cake", 0, ["cake", "cake show"], "cake "),
    ("cake -", 0, ["cake", "cake show"], "cake -arg "),
    ("help", 0, ["cake show", "cake make", "cake make again", "cake eat"], None),
])
def test_command_completer_completer(partial, index, commands, expected_output):
    """Verify the command completer will iterate through all possible matches
    of the user's current text.
    """

    # this is why global state is dangerous folks...
    recline.commands.COMMAND_REGISTRY = {}

    for app_command in commands:
        @command(name=app_command)
        def ut_command(arg: str):  # pylint: disable=unused-variable,unused-argument
            pass

    completer = CommandCompleter(recline.commands.COMMAND_REGISTRY)
    assert completer.completer(partial, index) == expected_output
