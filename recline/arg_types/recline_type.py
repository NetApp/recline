"""
Original © NetApp 2024

This module contains the abstract base class for all recline custom types
"""

from abc import ABC
import argparse
from typing import Any, List, Optional, Union


class UniqueParam(argparse.Action):  # pylint: disable=too-few-public-methods
    """Utility class that throws an error if more than one occurrence of param is found."""

    def __call__(self, parser, namespace, values, option_string=None):
        current_value = getattr(namespace, self.dest)
        # If the corresponding namespace attribute is not the default value or None raise error
        if current_value != self.default and current_value is not None:
            parser.error(f"Duplicate parameter \"{option_string}\"")
        # Update the namespace attribute with the given value
        setattr(namespace, self.dest, values)


class ReclineType(ABC):
    """The base class for all other custom types in recline. Default values for
    argparse are defined within each type.
    """

    metavar = "<value>"
    action = UniqueParam

    def __init__(self):
        self.arg_name = None

    def choices(self, eager=False) -> Optional[List[Any]]:  # pylint: disable=unused-argument,no-self-use
        """If an argument has a set list of choices that can be provided for it,
        then the type can specify to only allow that list
        """

        return None

    def completer(self, *args, **kwargs) -> List[Any]:  # pylint: disable=unused-argument,no-self-use
        """The completer function should return a list of values that are valid
        for the argument. This function will usually be implemented such that it
        is dynamic based on some API call or some current application state. If
        it is a static set of choices, it would be easier to use the choices
        method instead.
        """

        return [None]

    def nargs(self) -> Optional[Union[int, str]]:  # pylint: disable=no-self-use
        """The number of arguments that this type can accept. See the argparse
        documentation for details: https://docs.python.org/3/library/argparse.html#nargs
        """

        return None

    def validate(self, arg: str) -> Any:  # pylint: disable=no-self-use
        """The validate function has two uses. First, a type should verify that
        the user's input matches the data that the type accepts. Second, it should
        transform the data if necessary. For example, it might try to cast a string
        to an integer and if it can, return the integer value.

        If validation fails, a ReclineTypeError should be raised with an appropriate
        message for the user.
        """

        return arg
