"""
Copyright (C) 2019 NetApp Inc.
All rights reserved.

A test module for the cliche.arg_types.positional module
"""

import argparse
from contextlib import ExitStack as does_not_raise

import pytest

from cliche.arg_types.cliche_type_error import ClicheTypeError
from cliche.arg_types.positional import Positional


@pytest.mark.parametrize("user_input, expectation", [
    ("my_dir", does_not_raise()), ("", pytest.raises(ClicheTypeError)),
])
def test_positional(user_input, expectation):
    """Verify the Positional type will assert the user provided something"""

    def path_completer(*_, **__):
        """This completer would be called at runtime if the user pressed tab"""
        return []

    default_positional = Positional()
    assert default_positional.validate(user_input) == user_input
    assert default_positional.nargs() is None
    assert default_positional.completer()[0] is None

    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=Positional.define(completer=path_completer)().validate)

    with expectation:
        parsed_args = parser.parse_args([user_input])
        assert parsed_args.path == user_input


@pytest.mark.parametrize("user_input, data_type, expectation", [
    ("my_val", str, does_not_raise()), ("my_val", int, pytest.raises(ClicheTypeError)),
])
def test_positional_type(user_input, data_type, expectation):
    """Verify the Positional type will assert the user provided a correct type"""

    parser = argparse.ArgumentParser()
    parser.add_argument('value', type=Positional.define(data_type=data_type)().validate)
    with expectation:
        parsed_args = parser.parse_args([user_input])
        assert parsed_args.value == user_input
