Async Commands
==============

In a REPL environment, there are often many commands the user may be able to run.
Some commands may take a long time to complete and maybe there are other commands
that even give status about what the first command is doing. Here's an example
program that we will highlight below:

.. code-block:: Python

    """
    This application has some commands that can run in the background and some in
    the foreground only.
    """

    import asyncio

    import cliche
    from cliche.formatters.table_formatter import TableFormat


    PERCENT_COMPLETE = None


    @cliche.command
    async def deploy(duration: int = 30) -> TableFormat:
        """Runs a deployment operation over a period of time

        Args:
            duration: The amount of time to run for
        """

        global PERCENT_COMPLETE

        try:
            seconds_slept = 0
            while seconds_slept < duration:
                await asyncio.sleep(1)
                seconds_slept += 1
                PERCENT_COMPLETE = (seconds_slept / duration) * 100
            return [{'duration': duration}]
        except asyncio.CancelledError:
            print('I only managed to get %s out of %s seconds of sleep before you interrupted me' % (seconds_slept, duration))


    @cliche.command(name="deploy status")
    def deploy_status() -> None:
        """Get the current deployment status percentage of an ongoing operation"""

        if PERCENT_COMPLETE is None:
            print("No deployment has been started yet")
            return

        print("The current deployment is %s%% complete" % PERCENT_COMPLETE)


    cliche.run()

Writing an Async Command
------------------------

Writing a command that can be put in the background is easy. Simply add the ``async``
keyword while defining the function. This tells cliche that the command may be long
running and it allows the user of the application to execute the command and put it
in the background or foreground as desired.

In the body of your async command, it is recommended to use ``await`` with coroutines
where available to help make your command more responsive. Backgrounding and foregrounding
don't rely on this, but cancelling an async command can only be done on the next
switch of the event loop.

In our ``deploy`` command above, we've implemented a simple async sleep loop to
simulate something that takes a long time. We've declared the function with ``async def``
and inside the function body we've used ``await asyncio.sleep(1)`` inside the loop
to make long running behavior.

In this example, there is a ``try/except`` block around the async operation. This
is optional, but it allows our command to have special behavior in the case the user
cancels the command. We get one more opportunity to run and clean up if needed. In
this case, we elected to show the user a short message saying that we didn't get to
complete.

Executing an Async Command
--------------------------

From the user's perspective, there isn't too much that is different about an async
command. Commands are executed the same way as non-async commands::

    $ python examples/async.py
    > deploy -duration 5
    +----------+
    | Duration |
    +----------+
    | 5        |
    +----------+
    >

If the user knows that the command will take a long time, they may wish to run
it from the background to begin with. In this case, they can pass ``-background``
when starting the command::

    $ python examples/async.py
    > deploy -duration 5 -background
    ^Z
    Job 2 is running in the background
    >

Send an Async Command to the Background
---------------------------------------

If the command was started in the foreground and the users wishes to run other commands
while the first is executing, they can press ``ctrl+z`` to send it to the background.
When doing this, the command continues to execute, but the user is free to run other
commands as well::

    $ python examples/async.py
    > deploy -duration 30
    ^Z
    Job 1 is running in the background
    > deploy status
    The current deployment is 20.0% complete
    >

Bring a Backgrounded Command Back to the Foreground
---------------------------------------------------

After a command was sent to the background, the shell prints a message indicating
the job number associated with the command. The user may re-attach to the command
by using the ``fg`` builtin. This will bring the command back to the foreground
and once again block user input until the command has completed::

    > deploy -duration 30
    ^Z
    Job 2 is running in the background
    > deploy status
    The current deployment is 26.666666666666668% complete
    > fg -job 2
    +----------+
    | Duration |
    +----------+
    | 30       |
    +----------+
    >

If the command completed executing while in the background, it remains avaialable
for the user to foreground it in order to retrieve its result. In this case, the
user can expect to execute the ``fg`` command and the result would be printed immediately.

Once a command execution has finished and the result has been returned, whether
it finished in the foreground or it was foregrounded after completion, the entry
is cleaned up and it is no longer available to be foregrounded::

    > deploy -duration 30
    ^Z
    Job 3 is running in the background
    > fg -job 3
    +----------+
    | Duration |
    +----------+
    | 30       |
    +----------+
    > fg -job 3
    Could not find a running job for 3
    >
