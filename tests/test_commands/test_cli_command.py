"""
Copyright (C) 2019 NetApp Inc.
All rights reserved.

A test module for the cliche.commands.cli_command module
"""

from typing import List

import pytest

import cliche
from cliche.arg_types.choices import Choices
from cliche.arg_types.flag import Flag
from cliche.commands.cli_command import CLICommand
from cliche.formatters.table_formatter import TableFormat


# pylint: disable=bad-continuation,unused-argument
def unit_test_command(
    types: Choices.define(["type1", "type2", "type3"]),
    names: List[str],
    optional: str = "foo",
    optional2: bool = False,
    optional3: Flag = False,
) -> TableFormat:
    """This is a test command short description

    This is a test command long description

    Args:
        types: This is the types parameter
        names: This is the names parameter
        optional: This is the optional parameter
        optional2: This is the optional2 parameter
        optional3: This is the optional3 parameter
    """


def test_command_init():
    """Verify that given a function, the CLICommand parses it correctly and contains
    a list of parameters and docstrings for those parameters.
    """

    command = CLICommand(unit_test_command)
    assert command.name == "unit_test_command"
    assert len(command.required_args) == 2
    assert len(command.optional_args) == 3
    assert command.output_formatter is not None
    assert not command.hidden
    assert not command.is_alias


@pytest.mark.parametrize("is_hidden", [True, False])
def test_command_hidden(is_hidden):
    """Verify the command says it is hidden when appropriate"""

    def is_currently_hidden():
        return is_hidden

    def maybe_hidden_command():
        """This command can be hidden"""

    def staticly_hidden_command():
        """This command is always hidden or never hidden"""

    command = CLICommand(maybe_hidden_command, hidden=is_currently_hidden)
    assert command.hidden == is_hidden

    command = CLICommand(staticly_hidden_command, hidden=is_hidden)
    assert command.hidden == is_hidden


@pytest.mark.parametrize("arg_name, expected", [
    ("types", "  -types <type1|type2|type3> This is the types parameter"),
    ("names", "  -names <names> [names ...] This is the names parameter"),
    ("optional", "  -optional <optional> This is the optional parameter\n    Default: foo"),
    ("optional2", "  -optional2 <true|false> This is the optional2 parameter\n    Default: false"),
    ("optional3", "  -optional3 This is the optional3 parameter"),
])
def test_get_arg_help(arg_name, expected):
    """Verify we can generate help text for a given arg"""

    command = CLICommand(unit_test_command)
    for arg in command.required_args:
        if arg.name == arg_name:
            arg_help = command.get_arg_help(arg)
            assert arg_help == expected
    for arg in command.optional_args:
        if arg.name == arg_name:
            arg_help = command.get_arg_help(arg)
            assert arg_help == expected


def test_get_command_help():
    """Verify we can generate help text for the whole command"""

    command = CLICommand(unit_test_command)
    help_text = command.get_command_help()
    assert command.docstring.short_description in help_text
    assert command.docstring.long_description not in help_text
    for arg in command.required_args:
        arg_help = command.get_arg_help(arg)
        assert arg_help in help_text
    for arg in command.optional_args:
        arg_help = command.get_arg_help(arg)
        assert arg_help in help_text


def test_register_start():
    """Verify we can register a single command run run at the start of the applciation"""

    cliche.commands.START_COMMAND = None

    @cliche.command(atstart=True)
    def start_cmd():
        """This command will run at the start of the application"""

    assert (
        cliche.commands.START_COMMAND.func == start_cmd  # pylint: disable=comparison-with-callable
    )

    with pytest.raises(RuntimeError):
        @cliche.command(atstart=True)
        def another_start_cmd():  # pylint: disable=unused-variable
            """Can only have one start command"""

    cliche.commands.START_COMMAND = None


def test_register_exit():
    """Verify we can register a single command to run at the end of the applciation"""

    cliche.commands.EXIT_COMMAND = None

    @cliche.command(atexit=True)
    def exit_cmd():
        """This command will run at the exit of the application"""

    assert (
        cliche.commands.EXIT_COMMAND.func == exit_cmd  # pylint: disable=comparison-with-callable
    )

    with pytest.raises(RuntimeError):
        @cliche.command(atexit=True)
        def another_exit_cmd():  # pylint: disable=unused-variable
            """Can only have one exit command"""

    cliche.commands.EXIT_COMMAND = None
