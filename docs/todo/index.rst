Things To Do
============

This page is not part of the general documentation of the library. Rather it is
meant as a placeholder to add features or bugs that should be worked on at some
point in the library's lifetime.

Feature Enhancements
--------------------

This is a list of potential feature enhancements that could make the user's life
easier.

Multiple Output Choices
***********************

recline supports output formatting, but in the current version, you can only specify
a single output format type. It may make sense to support multiple output types
for a single command and to have the application user select between them at runtime.

This could look something like this:

.. code-block:: Python

    @recline.command(name='cake show')
    def show_cake() ->  Union[TableFormat, CSVFormat, JSONFormat]
        return cakes

In this case, TableFormat would be the default if the user didn't choose anything
explicitly. There would need to be some mechanism by which arguments were added to
the command based on the output types it supports.

Support Other Async Libraries
*****************************
We may want to support gevent, trio, tornado, etc. in addition to asyncio for async commands

Pipelines
*********

Something I was thinking would be useful is to implement pipes. For instance::

    ::> cake show -flavor chocolate
    +----+-------------+-----------+
    | ID | Cake Layers | Flavor    |
    +----+-------------+-----------+
    | 1  | 1           | chocolate |
    | 2  | 3           | chocolate |
    | 3  | 2           | chocolate |
    +----+-------------+-----------+
    ::> cake eat -id 1
    Yum, that was a good 1 layer chocolate cake
    ::> cake show -flavor chocolate | cake eat
    Yum, that was a good 3 layer chocolate cake
    Yum, that was a good 2 layer chocolate cake

In this example, we piped the output of the ``cake show`` command to the input
of the ``cake eat`` command. Normally, the ``cake eat`` command requires an ``id``
input, but it was able to take it from the table formatted output of the last
command in the chain.

Internally, I expect that each output formatter type may choose to implement a
pip_output function which returns a dict. That dict would have data names and
values and the names would then be matched to the inputs of the next command
in the pipe. If it didn't implement this, then the raw text of the output would
be taken and it would be up to the next command in the pipe to interpret it.

Variables
*********

Sometimes, it might be nice to not have to remember/type so much. For example, you might
have a value that you want to use in multiple commands and it is either complex
or long. The library should provide a way to save this value with a meaningful, user-
chosen name and reuse it later. For example::

    >:: echo hello world
    hello world
    >:: foo="this is the song that never ends; yes it goes on and on my friend"
    >:: echo $foo
    this is the song that never ends; yes it goes on and on my friend
    >:: shout $foo
    THIS IS THE SONG THAT NEVER ENDS; YES IT GOES ON AND ON MY FRIEND!
    >:: 

Here we saved a simple constant string value so that we could use it multiple times
without having to retype it. But this feature could also be used to save the result
of a command and use it again later::

    >:: add 3 5
    8
    >:: answer=$(add 3 5)
    >:: buy donuts -count $answer
    Here are your 8 donuts
    >:: 

Here, we ran the add command and saved its output as the value of a variable. Then
we can use that variable later in the session in other commands as input.

Wizards
*******

Often, a command might have one or more required arguments. Typically, when a user
doesn't provide all of the required arguments, the command will fail and show the
user the brief help for that command with a syntax to highlight which arguments are
required and which are optional.

This is fine, but it does give the user a sense of failure. What if we could do better?
Since recline focuses its efforts on an interactive experience, why shouldn't it be
able to prompt the user for those missing inputs before continuing? That way, the
user can gain familiarity with the command and not receive a failure.

Here's an example script that we will use:

.. code-block:: Python

    import recline
    from recline.arg_types.choices import Choices

    @recline.command(name="pitch baseball")
    def pitch_baseball(grip: str, speed: int, handedness: Choices.define(["right", "left"]) = "right") -> str:
        """Throw one right down the plate and strike out the batter if you can!

        Arguments:
            grip: How do you want to hold the ball?
            speed: How fast are you going to throw the ball?
            handedness: Which hand will you pitch with?
        """

        if speed > 95:
            print("Strike!")
        else:
            print("That ball is out of here!")


recline.relax(prompt=">:: ")

This is how it would look without this feature::

    $ python wizard_test.py
    >:: pitch baseball
    usage: wizard_test.py -grip <grip> -speed <int> [-handedness <value>]
    wizard_test.py: error: the following arguments are required: -grip, -speed
    >::

With the feature, it might look like this instead::

    $ python wizard_test.py
    >:: pitch baseball
    A value is required for grip: two finger
    A value is required for speed: 96
    Strike!
    >::

Known Issues
------------

Issues can be filed and tracked via GitHub: https://github.com/NetApp/recline/issues

Status Codes
************

There is some notion of status/exit codes in the shell.py file, but they don't
make it all the way out to the external shell when operating in non-interactive
mode::

    $ python examples/cake.py -c "cake make"
    usage: cake.py -layers <int{2-10}> -flavor <value>
    cake.py: error: the following arguments are required: -layers, -flavor
    $ echo $?
    0
    $
