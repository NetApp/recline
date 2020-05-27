Command Help and Man Pages
==========================

A CLI application is only as good as its documentation. Since cliche is meant to be a
documentation first library, it only makes sense that it provides good documentation
to your users as well. And this documentation should come from the same source as the
implementation so that they stay in sync. Take our ``cake make`` command from before
and let's add just a bit more to its docstring:

.. code-block:: Python

    @cliche.command(name='cake make')
    def make_cake(
        layers: RangedInt.define(min=2, max=10),
        flavor: Choices.define(['chocolate', 'vanilla', 'marble']),
    ) -> None:
        """Make a cake with the specified number of layers

        Pat-a-cake, pat-a-cake, baker's man.
        Bake me a cake as fast as you can
        Pat it, and prick it, and mark it with "B"
        And put it in the oven for Baby and me!

        Args:
            layers: The number of layers to make must be provided which is
                an integer between 2 and 10.
            flavor: The type of cake to make.

        Examples:
            layer_validation_failure:
                ::> cake make -flavor chocolate -layers 1
                layers: 1 is not an integer in the range {2-10}.
            type_validation_failure:
                ::> cake make -flavor bogus -layers 2
                flavor: "bogus" must be one of chocolate, vanilla, marble.
            success:
                ::> cake make -flavor chocolate -layers 2
                Adding ingredients
                Mixing the batter
                Baking the cake
                Made a 1 layer chocolate cake. Sorry, I burned one layer.
                ::>
        """

        cakes.append(
            OrderedDict([('cake layers', layers - 1), ('flavor', type)]),
        )
        print('Adding ingredients')
        sleep(2)
        print('Mixing the batter')
        sleep(3)
        print('Baking the cake')
        sleep(5)
        print(
            'Made a %s layer %s cake. Sorry, I burned one layer.' %
            (layers - 1, type)
        )


In this example, we've added a more detailed description including multiple paragraphs
and some examples of the command being run along with its output. This should give
your users all the information they need in order to know how to use the command.

Command Help
------------

If the user wants to list the help for the command, they can use the ``-help`` argument
and get most of the details from our declaration and description printed right in
line with the command prompt::

    ::> cake make -help
    Make a cake with the specified number of layers

    Required arguments:
    -layers <int{2-10}> The number of layers to make must be provided which is an integer
                        between 2 and 10.
    -flavor <chocolate|vanilla|marble> The type of cake to make.
    ::>

Man Pages
---------

Notice the examples are not shown here and neither is the longer part of the description.
Usually, when a user wants to be reminded of how a command works, this information
would be too much and would clutter up their screen. But what if they need more details?
This is where cliche uses the UNIX style manpage system. If a user types ``man cake make``
then they will be shown the following in a full screen display::

    cake make                         cake.py                          cake make


    NAME
        cake make -- Make a cake with the specified number of layers

    SYNOPSIS
        cake make -layers <int{2-10}> -flavor <chocolate|vanilla|marble>
    DESCRIPTION
        Pat-a-cake, pat-a-cake, baker's man.
        Bake me a cake as fast as you can
        Pat it, and prick it, and mark it with "B"
        And put it in the oven for Baby and me!
    OPTIONS
        Required:
        -layers <int{2-10}> The number of layers to build the cake from.

        -flavor <chocolate|vanilla|marble> The flavor of cake to make.

    EXAMPLES
        layer_validation_failure:
        ::> cake make -flavor chocolate -layers 1
        layers: 1 is not an integer in the range {2-10}.
        type_validation_failure:
        ::> cake make -flavor bogus -layers 2
        flavor: "bogus" must be one of chocolate, vanilla, marble.
        success:
        ::> cake make -flavor chocolate -layers 2
        Adding ingredients
        Mixing the batter
        Baking the cake
        Made a 1 layer chocolate cake. Sorry, I burned one layer.
        ::> 
    
    (END)

This gives them access to all the information they will need including a detailed
description and examples of running the command. All commands get ``-help`` arguments
and ``man`` page entries for free.