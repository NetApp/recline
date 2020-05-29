"""
This package contains the various custom type definitions for CLI command parameters.
If you are defining a CLI command function that takes input with restrictions,
you may want to use a type annotation to allow recline to do the checking for you
before your function ever gets invoked. For example:

from recline.arg_types import Choices

@recline.command
def commit(branch: Choices.define(['dev', 'beta', 'stable'])) -> None:
    # the function can now assume that branch has already been validated to be
    # one of the options above before we got here
"""
