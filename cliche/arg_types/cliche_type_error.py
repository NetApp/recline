"""
This module contains the error class that is raised when there is a type error
when validating user input.
"""

import inspect

from cliche.arg_types.cliche_type import ClicheType


class ClicheTypeError(Exception):
    """This is a custom exception type that tries to reach into the previous frame
    and get some information if it is present in order to make its error message
    better.
    """

    def __init__(self, message: str):
        # Reach up frame and see if we can attach the arg name to the message
        # If we can't for some reason, it won't get attached
        try:
            type_instance = inspect.currentframe().f_back.f_locals.get("self")
            if isinstance(type_instance, ClicheType) and type_instance.arg_name is not None:
                super().__init__("%s: %s" % (type_instance.arg_name, message))
        except Exception:  # pylint: disable=broad-except
            super().__init__(message)
