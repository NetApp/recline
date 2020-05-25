"""
Copyright (C) 2019 NetApp Inc.
All rights reserved.

A test module for the cliche.arg_types.choices module
"""

from contextlib import ExitStack as does_not_raise

import pytest

from cliche.arg_types.choices import Choices
from cliche.arg_types.cliche_type_error import ClicheTypeError


@pytest.mark.parametrize("valid_choices, inexact, user_choice, expectation", [
    (["chocolate", "vanilla"], False, "chocolate", does_not_raise()),
    (["chocolate", "vanilla"], False, "strawberry", pytest.raises(ClicheTypeError)),
    ([], False, "anything", pytest.raises(ClicheTypeError)),
    (["chocolate", "vanilla"], True, "cho*", does_not_raise()),
])
def test_choices(valid_choices, inexact, user_choice, expectation):
    """Verify the Choices type will be picky about which values are allowed"""

    choices = Choices.define(valid_choices, inexact=inexact)()
    assert choices.completer() == valid_choices
    with expectation:
        choices.validate(user_choice)


@pytest.mark.parametrize("valid_choices, cache, user_choice, expectation, func_access", [
    (["chocolate", "vanilla"], True, "chocolate", does_not_raise(), 1),
    (["chocolate", "vanilla"], False, "chocolate", does_not_raise(), 3),
    (["chocolate", "vanilla"], True, "strawberry", pytest.raises(ClicheTypeError), 1),
    ([], "anything", False, pytest.raises(ClicheTypeError), 2),
])
def test_choices_callable(valid_choices, cache, user_choice, expectation, func_access):
    """Verify the Choices type will be picky about which values are allowed when
    the input to the class is a callable.
    """

    times_called = 0

    def get_choices():
        nonlocal times_called
        times_called += 1
        return valid_choices

    choices = Choices.define(get_choices, cache_choices=cache)()
    assert choices.choices() is None
    assert choices.choices(eager=True) == valid_choices
    assert choices.completer() == valid_choices
    with expectation:
        choices.validate(user_choice)
        assert times_called == func_access
