"""
Original © NetApp 2024

This application has some commands that can run in the background and some in
the foreground only.
"""

import asyncio

import recline
from recline.formatters.table_formatter import TableFormat


PERCENT_COMPLETE = None


@recline.command
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


@recline.command(name="deploy status")
def deploy_status() -> None:
    """Get the current deployment status percentage of an ongoing operation"""

    if PERCENT_COMPLETE is None:
        print("No deployment has been started yet")
        return

    print("The current deployment is %s%% complete" % PERCENT_COMPLETE)


recline.relax()
