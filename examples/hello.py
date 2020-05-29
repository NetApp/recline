"""
A "hello world" application for CLI commands
"""

from typing import List

import recline


@recline.command
def hello(name: str = None) -> None:
    """A basic hello world

    You can greet just about anybody with this command if they give you their name!

    Args:
        name: If a name is provided, the greeting will be more personal
    """
    response = "I'm at your command"
    if name:
        response += ", %s" % name
    print(response)


@recline.command(name="group hello")
def group_hello(names: List[str], formal: bool = False) -> None:
    """A less-basic hello world

    You can greet several people with this command if they give you their names!

    Args:
        names: Names must be provided so that the greeting will be more personal
        formal: Formal language does not use contractions
    """
    if formal:
        response = 'I am at your command, %s' % names
    else:
        response = "I'm at your command, %s" % names
    print(response)


recline.relax(history_file='.hello_history.txt')
