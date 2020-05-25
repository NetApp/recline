"""
A Flag type allows the CLI command writer to specify an argument that behaves
like a boolean flag. The difference between this and declaring an argument as a
bool is that no "true" or "false" input is expected of the user if the argument
is a flag. If it is a bool, then the user must provide either "true" or "false"
explicitly on the command line.

@cliche.command
def ls(l: Flag = None) -> None:
    # If the user provided "-l" then l will be set to True. Else l will be None
"""

from cliche.arg_types.cliche_type import ClicheType


class Flag(ClicheType):
    """A simple flag argument which will be set to true if provided"""
    action = 'store_true'
