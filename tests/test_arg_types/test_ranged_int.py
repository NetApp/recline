"""
Copyright (C) 2019 NetApp Inc.
All rights reserved.

A test module for the cliche.arg_types.ranged_int module
"""

from contextlib import ExitStack as does_not_raise

import pytest

from cliche.arg_types.cliche_type_error import ClicheTypeError
from cliche.arg_types.ranged_int import RangedInt


@pytest.mark.parametrize("min_val, max_val, user_input, expectation", [
    (2, 10, 5, does_not_raise()), (0, None, 100, does_not_raise()),
    (None, 100, -50, does_not_raise()), (None, None, 100, does_not_raise()),
    (2, 10, 1, pytest.raises(ClicheTypeError)), (0, None, -1, pytest.raises(ClicheTypeError)),
    (None, 100, 105, pytest.raises(ClicheTypeError)),
    (2, 10, "foo", pytest.raises(ClicheTypeError)),
])
def test_choices(min_val, max_val, user_input, expectation):
    """Verify the RangedInt type will assert the user provided something in the
    specified range"""

    ranged_int = RangedInt.define(min=min_val, max=max_val)()
    with expectation:
        ranged_int.validate(user_input)
