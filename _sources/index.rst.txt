Recline: A Documentation First CLI Library
==========================================

We automate so that we can be lazy, but writing argparse-based command line applications
can become tedious, repetitive, and tired. Let this library free you from that burden.

This library helps you quickly implement an interactive, command-based application in Python
without all the work associated with implementing a frieldly and featureful CLI application.

.. code-block:: Python

    import recline

    @recline.command
    def hello(name: str = None) -> None:
    """A basic hello world

    Args:
        name: If a name is provided, the greeting will be more personal
    """
    response = "I'm at your command"
    if name:
        response += ", %s" % name
    print(response)

    recline.relax()

Running the above application would produce the following result::

    $ python hello.py
    > help
    Available Commands:

    hello - A basic hello world

    Built-in Commands
    -----------------
    exit - Exit the application
    help - Display a list of available commands and their short description
    man - Display the full man page for a given command
    > hello ?
    A basic hello world

    Optional arguments:
    -name <name> If a name is provided, the greeting will be more personal
        Default: None
    > hello
    I'm at your command
    > hello -name Dave
    I'm at your command, Dave
    > exit
    $

Documentation First
-------------------

We all know that writing documentation is very important and yet it can easily become
and afterthought or a nice to have if we're not diligent. This is often because it
means duplicating a piece of your implementation in words, effectively writing the
same thing twice. Recline strives to deduplicate this work by taking a documentation
first attitude where your documentation *becomes* the implementation without additional
work from you.

Interactive
-----------

The default mode is to run a REPL interface where a prompt is given to the user, the
user types one of the available commands, the application processes it, displays the
result, and then control is returned to the user once more.

But if your user isn't expected to or doesn't always want to run multiple commands,
you also get a more traditional command-line interface for free.

Command-based
-------------

The application will be command based. Each command will have one or more words
that identify the command. It may also have one or more arguments that augment or
vary the action that command will take.

Batteries included
------------------

While the library is designed to be easy to implement for simple or small applications,
it also comes with full power features for larger use cases including:

* Tab completion
* Input verification
* Output formatting
* Debugger integration

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    before_getting_started/index
    quickstart/index
    input_output/index
    help_text/index
    tab_completion/index
    command_chaining/index
    async_commands/index
    todo/index
    api_reference/modules
