"""
Copyright (C) 2019 NetApp Inc.
All rights reserved.

A test module for the recline.arg_types.recline_type module
"""

import argparse
from contextlib import ExitStack as does_not_raise

import pytest

from recline.arg_types.recline_type import UniqueParam


@pytest.mark.parametrize('user_input, expectation', [
    ([], does_not_raise()), (['-arg', 'foo'], does_not_raise()),
    (['-arg2', 'foo'], does_not_raise()),
    (['-arg', 'foo', '-arg', 'bar'], pytest.raises(SystemExit)),
    (['-arg', 'foo', '-arg2', 'bar'], does_not_raise()),
    (['-arg2', 'foo', '-arg2', 'bar'], pytest.raises(SystemExit)),

])
def test_unique_param(user_input, expectation):
    """Verify we get an error if we try to parse input that duplicates a unique
    parameter in our definition
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-arg', action=UniqueParam)
    parser.add_argument('-arg2', action=UniqueParam)
    with expectation:
        parser.parse_args(user_input)
