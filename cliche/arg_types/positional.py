"""
A Positional type allows the CLI command writer to specify an argument that the
user will provide positionally. That is, instead of the user typing
"-arg_name argvalue", they can just type "argvalue". For example:

@cliche.command
def ls(path: Positional = ".") -> None:
    # If the user provided "ls my_dir", then path will be set to "my_dir". If the
    # user just said "ls", then path will be set to ".".
"""

from cliche.arg_types.cliche_type import ClicheType
from cliche.arg_types.cliche_type_error import ClicheTypeError


class Positional(ClicheType):
    """The Positional type allows the user to not have to specify the arugment name"""

    @staticmethod
    def define(completer=None, data_type=str):
        """Allows a Positional type to be defined with its own completer function"""

        class _Positional(Positional):
            def __init__(self):
                if completer:
                    self.completer = completer
                self.data_type = data_type
                super().__init__()

            def validate(self, arg: str):
                if arg is None or arg == "":
                    raise ClicheTypeError("Value cannot be empty")
                try:
                    return self.data_type(arg)
                except Exception:
                    raise ClicheTypeError(
                        "Cannot parse %s as a valid %s" % (arg, data_type.__name__)
                    )

        return _Positional
