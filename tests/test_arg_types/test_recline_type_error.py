"""
Tests for recline.arg_types.recline_type_error
"""

import inspect
import unittest.mock as mock

import pytest

from recline.arg_types.recline_type import ReclineType
from recline.arg_types.recline_type_error import ReclineTypeError


class _ConcreteReclineType(ReclineType):
    """Minimal concrete ReclineType for testing."""

    def validate(self, arg):
        raise ReclineTypeError("bad value")


def test_recline_type_error_with_arg_name():
    """When raised from within a ReclineType.validate(), the arg_name should be
    prepended to the message.
    """

    type_instance = _ConcreteReclineType()
    type_instance.arg_name = "my_param"
    with pytest.raises(ReclineTypeError) as exc_info:
        type_instance.validate("something")
    assert "my_param: bad value" in str(exc_info.value)


def test_recline_type_error_without_arg_name():
    """When raised from within a ReclineType.validate() but arg_name is None,
    the message should be used as-is (the if-condition does not include the name).
    """

    type_instance = _ConcreteReclineType()
    type_instance.arg_name = None
    with pytest.raises(ReclineTypeError) as exc_info:
        type_instance.validate("something")
    # arg_name is None, so the name prefix is not added
    assert str(exc_info.value) == "bad value"


def test_recline_type_error_bare():
    """When raised outside of a ReclineType context, the message should be used as-is."""

    with pytest.raises(ReclineTypeError) as exc_info:
        raise ReclineTypeError("standalone error")
    assert str(exc_info.value) == "standalone error"


def test_recline_type_error_frame_inspection_failure(monkeypatch):
    """When frame inspection raises an exception, the plain message should still be set."""

    def raise_error():
        raise RuntimeError("frame inspection failed")

    monkeypatch.setattr(inspect, "currentframe", raise_error)

    with pytest.raises(ReclineTypeError) as exc_info:
        raise ReclineTypeError("fallback message")
    assert str(exc_info.value) == "fallback message"
