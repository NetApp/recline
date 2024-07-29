"""
Original © NetApp 2024

This package contains the base command class and the builtin command for all
recline-based applications to use.
"""

COMMAND_REGISTRY = {}
START_COMMAND = None
EXIT_COMMAND = None

class ReclineCommandError(Exception):
    """If there is an error while executing a command, this exception should be
    raised an an error will be printed to the console.
    """

__all__ = ['COMMAND_REGISTRY', 'EXIT_COMMAND', 'START_COMMAND', 'ReclineCommandError']
