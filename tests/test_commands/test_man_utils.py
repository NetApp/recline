"""
Copyright (C) 2019 NetApp Inc.
All rights reserved.

A test module for the recline.commands.man_utils module
"""

from inspect import Parameter

import pytest

from recline.commands import man_utils
from recline.commands.cli_command import CLICommand
from recline.vendor.docstring_parser.parser.common import DocstringMeta


@pytest.mark.parametrize("text, screen_width, prefix, output", [
    ("", 5, 0, ""), ("Hi", 5, 0, "Hi"), ("Hello", 10, 0, "Hello"),
    (
        "Hello there, fellow tester", 10, 0,
        "Hello\n"
        "there, fe-\n"
        "llow\n"
        "tester"
    ),
    (
        "Hello there,\nfellow tester", 10, 0,
        "Hello\n"
        "there,\n"
        "fellow te-\n"
        "ster"
    ),
    (
        "Hello there,\n\nfellow tester", 10, 0,
        "Hello\n"
        "there,\n\n"
        "fellow te-\n"
        "ster"
    ),
    (
        "Hello there, fellow tester", 9, 0,
        "Hello th-\n"
        "ere,\n"
        "fellow\n"
        "tester"
    ),
    (
        "Hello there, fellow tester", 12, 3,
        "Hello th-\n"
        "   ere,\n"
        "   fellow\n"
        "   tester"
    ),
])
def test_wrapped_string(text, screen_width, prefix, output):
    """Verify that we can wrap a string given a screen width. We should do our
    best to break on word boundaries when it makes sense and otherwise we'll
    hyphenate.
    """

    assert man_utils.wrapped_string(text, screen_width, prefix=prefix) == output


@pytest.mark.parametrize("command_name, args, kwargs, short_doc, long_doc, examples", [
    (
        "test command", ["foo"], {"bar": None}, "this is a test command",
        "this is a long desc", {"example1": "example1 text", "example2": "example2 text"},
    ),
    (
        "testcommand", ["foo", "bar"], {}, "this is a test command", "", {},
    ),
    (
        "testcommand", [], {}, "this is a test command", "", {},
    ),
])
# pylint: disable=too-many-arguments
def test_generate_help_text(command_name, args, kwargs, short_doc, long_doc, examples):
    """Verify that we generate an expected man page for a given command. I'm not
    going to verify all the formatting here, just the basics. Makes sure that
    all the pieces make it to the page and that it doesn't blow up. Format testing
    will be done visually which I think is acceptable.
    """

    command_class = CLICommand(lambda: None, name=command_name)
    command_class.name = command_name
    command_class.docstring.short_description = short_doc
    command_class.docstring.long_description = long_doc
    command_class.required_args = [
        Parameter(arg, Parameter.POSITIONAL_ONLY) for arg in args
    ]
    command_class.optional_args = [
        Parameter(arg, Parameter.KEYWORD_ONLY, default=val)
        for arg, val in kwargs.items()
    ]
    if args or kwargs:
        command_class.docstring.meta = [DocstringMeta(["arg"], "")]
    for label, description in examples.items():
        command_class.docstring.meta.append(
            DocstringMeta(["examples", label], description)
        )

    help_text = man_utils.generate_help_text(1000, command_class)
    text_pieces = [spec[0] for spec in help_text]
    help_text = ''.join(text_pieces)
    assert command_name in help_text
    for arg in args:
        assert arg in help_text
    for kwarg in kwargs.keys():
        assert kwarg in help_text
    assert short_doc in help_text
    assert long_doc in help_text
    for label, description in examples.items():
        assert label in help_text
        assert description in help_text
