"""
A Remainder type allows the CLI command writer to specify that an argument should
consume all of the rest of the input from the CLI and that it will be interpreted
inside of the command handler function.

@recline.command
def search(query: Remainder) -> None:
    # The user might use this command like "search stuff I want to know about"
    # and the query parameter would be filled with the value "stuff I want to know about"
"""

import argparse

from recline.arg_types.recline_type import ReclineType


class Remainder(ReclineType):
    """The Remainder type will capture all of the remaining input from the user
    into a single parameter, even if that input contained spaces which would
    normally be considered multiple values
    """

    @staticmethod
    def define(completer=None):
        """Allows a Remainder type to be defined with its own completer function"""

        class _Remainder(Remainder):
            metavar = '<value>'

            def __init__(self):
                if completer:
                    self.completer = completer
                super().__init__()

        return _Remainder

    def nargs(self):
        return argparse.REMAINDER
