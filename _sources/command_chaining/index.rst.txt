Shell Behavior
==============

While using an application built with the recline library, there is a common set of
shell functionality that is provided for you by the library. These will be familiar
to you if you are used to a unix style shell, like bash.

Command Chaining
----------------

There are three different command chaining operators, ``;``, ``&&``, and ``||``.
All three of these operators allow you to chain multiple commands on the same line
and then execute them as a group. The operator you choose will affect how the
commands are processed.

In the following example outputs, this toy program will be used for illustrative purposes:

.. code-block:: Python

    import recline
    from recline.commands import ReclineCommandError

    @recline.command
    def success():
        """This command will always succeed when run"""

        print("success!")

    @recline.command
    def failure():
        """This command will always fail when run"""

        raise ReclineCommandError("I'm a bad function")

    recline.relax(prompt="chaining test> ")

.. warning::
    For all of the operators below, if an :ref:`async command <async-commands>` is
    run in the background, using the -background flag, then it will always be
    considered as a success for the purposes of the operators. If the command is
    run in the foreground (the default), then its success or failure will be
    considered just like a synchronous command.

; Operator
**********

When the ``;`` operator is used, all chained commands will be run regardless of
the success or failure of the previous command in the chain. For example::

    chaining test> success; failure
    success!
    I'm a bad function
    chaining test> failure; success
    I'm a bad function
    success!
    chaining test> success; failure; success
    success!
    I'm a bad function
    success!
    chaining test>

&& Operator
***********

When the ``&&`` operator is used, the chain of commands will halted whenever a
command in the chain fails and no commands after that point will be run. It is
meant to be used when one command depends on another succeeding. For example::

    chaining test> success && failure
    success!
    I'm a bad function
    chaining test> failure && success
    I'm a bad function
    chaining test> success && failure && success
    success!
    I'm a bad function
    chaining test>

|| Operator
***********

When the ``||`` operator is used, the chain of commands will halted whenever a
successful command is executed. Commands after that point will not be run. It is
meant to provide alternatives in case something fails. For example::

    chaining test> failure || success
    I'm a bad function
    success!
    chaining test> success || failure
    success!
    chaining test> failure || success || success
    I'm a bad function
    success!
    chaining test>
