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

Support gevent
**************
We may want to support gevent in addition to asyncio for async commands

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
choosen name and reuse it later. For example::

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
