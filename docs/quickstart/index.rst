Quickstart
==========

After installing the package, you can get started with a few lines in ``hello.py``:

.. code-block:: Python

    import recline

    @recline.command
    def hello(name: str = None) -> None:
        """A basic hello world

        You can greet just about anybody with this command if they give you
        their name!

        Args:
            name: If a name is provided, the greeting will be more personal
        """
        response = "I'm at your command"
        if name:
            response += ", %s" % name
        print(response)

    recline.relax()

Interactive Mode
----------------

The default mode when a recline applciation is run is an interactive style. Running
our above ``hello.py`` results in the following output::

    $ python hello.py
    > help
    Available Commands:

    hello - A basic hello world You can greet just about anybody with this command if

    Built-in Commands
    -----------------
    exit - Exit the application
    help - Display a list of available commands and their short description
    man - Display the full man page for a given command
    > hello ?
    A basic hello world You can greet just about anybody with this command if

    Optional arguments:
    -name <name> If a name is provided, the greeting will be more personal
        Default: None
    > hello
    I'm at your command
    > hello -name Dave
    I'm at your command, Dave
    > exit
    $


Non-interactive mode
--------------------

If you would like to use the application as part of a larger script, it is much
easier to do in a non-interactive way. This is also possible using recline without
needing to change the application. Here's an example::

    $ python hello.py -c "hello -name Dave"
    I'm at your command, Dave
    $
