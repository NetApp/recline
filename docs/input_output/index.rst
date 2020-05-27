Input and Output
================

In the following examples, we will be discussing this code:

.. code-block:: Python

    from collections import OrderedDict

    import cliche
    from cliche.arg_types.ranged_int import RangedInt
    from cliche.arg_types.choices import Choices
    from cliche.formatters.table_formatter import TableFormat


    cakes = []


    @cliche.command(name='cake make')
    def make_cake(
        layers: RangedInt.define(min=2, max=10),
        flavor: Choices.define(['chocolate', 'vanilla', 'marble']),
    ) -> None:
        """Make a cake with the specified number of layers

        Args:
            layers: The number of layers to make must be provided which is
                an integer between 2 and 10.
            flavor: The type of cake to make.
        """

        cakes.append(
            OrderedDict([('cake layers', layers - 1), ('flavor', type)]),
        )
        print(
            'Made a %s layer %s cake. Sorry, I burned one layer.' %
            (layers - 1, type)
        )


    @cliche.command(name='cake show')
    def show_cake() -> TableFormat:
        """Show all of our completed cake work"""

        return cakes


    cliche.run(history_file='.cake_history.txt', prompt='::> ')


Which produces the following commands::

    ::> help
    Available Commands:

    cake make - Make the specified number of cakes
    cake show - Show all of our completed cake work

    Built-in Commands
    -----------------
    exit - Exit the application
    help - Display a list of available commands and their short description
    man - Display the full man page for a given command

Input Checking
--------------

In the example above, the ``cake make`` command takes two required parameters, number and type.
The layers parameter must be between 2 and 10 and this is checking is done by the
cliche library itself and only after the parameter has been verified will the command
actually be invoked. Here's an example of what it looks like if the argument passed
does not match the requirements::

    ::> cake make -flavor chocolate -layers 1
    layers: "1" is not an integer in the range {2-10}.
    ::> cake make -flavor bogus -layers 2
    flavor: "bogus" must be one of chocolate, vanilla, marble.


If the user provides valid inputs, then the command will be invoked and its function
body will execute::

    ::> cake make -flavor chocolate -layers 2
    Made a 1 layer chocolate cake. Sorry, I burned one layer.
    ::> cake make -flavor chocolate -layers 5
    Made a 4 layer chocolate cake. Sorry, I burned one layer.

Output Formatting
-----------------

There are often two kinds of commands. Commands that Create, Update, or Delete are
one type, and commands that Read values are another. For commands that are about
reading and displaying data, it is often useful to run that data through some sort
of common formatting so that similar commands look similar to the user. In our cake
application, the ``cake show`` command lists the cakes that have been made. Here's
what the output might look like::

    ::> cake show
    +-------------+-----------+
    | Cake Layers | Flavor    |
    +-------------+-----------+
    | 1           | chocolate |
    | 4           | chocolate |
    +-------------+-----------+


In our implementation code, all we needed to do was to return data that was in a
tablular sort of format (in this case, an iterable which contains key/value pairs of data).
The cliche library provides a common TableFormat class which knows how to construct
the table shown above based on the sizes of the headers and values in the output.
