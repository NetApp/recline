"""
Original © NetApp 2024

A test module for the recline.commands.cli_command module
"""

from typing import Annotated

import pytest

import recline
from recline.arg_types.choices import Choices
from recline.arg_types.flag import Flag
from recline.arg_types.positional import Positional
from recline.commands.cli_command import CLICommand
from recline.formatters.output_formatter import OutputFormatter
from recline.formatters.table_formatter import TableFormat


# pylint: disable=bad-continuation,unused-argument
def unit_test_command(
    types: Choices.define(["type1", "type2", "type3"]),
    names: list[str],
    optional: str = "foo",
    optional2: bool = False,
    optional3: Flag = False,
) -> Annotated[list[dict[str, str]], TableFormat]:
    """This is a test command short description

    This is a test command long description

    Args:
        types: This is the types parameter
        names: This is the names parameter
        optional: This is the optional parameter
        optional2: This is the optional2 parameter
        optional3: This is the optional3 parameter
    """

    return []


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

    recline.commands.START_COMMAND = None

    @recline.command(atstart=True)
    def start_cmd():
        """This command will run at the start of the application"""

    assert (
        recline.commands.START_COMMAND.func == start_cmd  # pylint: disable=comparison-with-callable
    )

    with pytest.raises(RuntimeError):
        @recline.command(atstart=True)
        def another_start_cmd():  # pylint: disable=unused-variable
            """Can only have one start command"""

    recline.commands.START_COMMAND = None


def test_register_exit():
    """Verify we can register a single command to run at the end of the applciation"""

    recline.commands.EXIT_COMMAND = None

    @recline.command(atexit=True)
    def exit_cmd():
        """This command will run at the exit of the application"""

    assert (
        recline.commands.EXIT_COMMAND.func == exit_cmd  # pylint: disable=comparison-with-callable
    )

    with pytest.raises(RuntimeError):
        @recline.command(atexit=True)
        def another_exit_cmd():  # pylint: disable=unused-variable
            """Can only have one exit command"""

    recline.commands.EXIT_COMMAND = None


class _SimpleFmt(OutputFormatter):  # pylint: disable=too-few-public-methods
    """A simple formatter used for annotation coverage tests."""

    def format_output(self, results):
        pass


def cmd_with_various_types(
    float_arg: float,
    dict_arg: dict,
    list_type_arg: list[Choices.define(["a", "b"])],
    pos_arg: Positional = ".",
) -> _SimpleFmt:
    """Command for testing various annotation types.

    Args:
        float_arg: A float argument.
        dict_arg: A dict argument.
        list_type_arg: A list of choices.
        pos_arg: A positional argument.
    """


def test_output_formatter_direct_return_type():
    """Verify CLICommand recognises an OutputFormatter subclass as return type directly."""

    cmd = CLICommand(cmd_with_various_types)
    assert cmd.output_formatter is not None


def test_cli_command_str():
    """Verify CLICommand.__str__ returns a useful string representation."""

    cmd = CLICommand(cmd_with_various_types)
    result = str(cmd)
    assert "cmd_with_various_types" in result


def test_float_and_dict_annotations():
    """Verify CLICommand parses float and dict annotations without error."""

    cmd = CLICommand(cmd_with_various_types)
    float_spec = None
    dict_spec = None
    list_spec = None
    for arg in cmd.required_args:
        if arg.name == "float_arg":
            float_spec = arg
        if arg.name == "dict_arg":
            dict_spec = arg
        if arg.name == "list_type_arg":
            list_spec = arg
    assert float_spec is not None
    assert dict_spec is not None
    assert list_spec is not None


def test_positional_arg_metavar_and_help():
    """Verify get_arg_metavar and get_arg_help work for Positional args."""

    cmd = CLICommand(cmd_with_various_types)
    for arg in cmd.optional_args:
        if arg.name == "pos_arg":
            metavar = cmd.get_arg_metavar(arg)
            assert f"<{arg.name}>" == metavar
            help_text = cmd.get_arg_help(arg)
            assert arg.name in help_text


def test_get_arg_description_indent_none():
    """Verify get_arg_description with indent=None returns inline description."""

    cmd = CLICommand(cmd_with_various_types)
    for arg in cmd.required_args:
        if arg.name == "float_arg":
            desc = cmd.get_arg_description(arg, indent=None)
            assert "float" in desc.lower()
    """Verify get_command_help handles a command with no docstring gracefully."""

    def no_doc_cmd():
        pass

    cmd = CLICommand(no_doc_cmd)
    help_text = cmd.get_command_help()
    # Should not raise; short_description is None → skip
    assert isinstance(help_text, str)


def test_get_command_help_only_optional_args():
    """Verify get_command_help handles a command with only optional args."""

    def opt_only_cmd(opt: str = "default"):
        """Command with only optional args.

        Args:
            opt: An optional argument.
        """

    cmd = CLICommand(opt_only_cmd)
    help_text = cmd.get_command_help()
    assert "Optional arguments" in help_text
    assert "Required arguments" not in help_text


def test_get_command_help_only_required_args():
    """Verify get_command_help handles a command with only required args (no optional block)."""

    def req_only_cmd(req: str):
        """Command with only required args.

        Args:
            req: A required argument.
        """

    cmd = CLICommand(req_only_cmd)
    help_text = cmd.get_command_help()
    assert "Required arguments" in help_text
    assert "Optional arguments" not in help_text
