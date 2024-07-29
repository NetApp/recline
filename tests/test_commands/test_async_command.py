"""
Original © NetApp 2024

A test module for the recline.commands.async_command module
"""

import asyncio

import pytest

import recline
from recline.commands.async_command import AsyncCommand


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_run():
    """Verify that if given a coroutine, the AsyncCommand will register and then
    run the coroutine when in the foreground.
    """

    test_result = "This is the answer"

    @recline.command(name="test")
    async def test_coro():  # pylint: disable=unused-variable
        return test_result

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    job_pid = thread.job_pid
    assert recline.JOBS[job_pid] == thread
    assert recline.NEXT_JOB_PID == job_pid + 1
    thread.start()
    assert thread.foreground() == test_result
    assert job_pid not in recline.JOBS


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_run_background():
    """Verify that if given a coroutine, the AsyncCommand will register and then
    run the coroutine when in the background and we can retrieve the result.
    """

    test_result = "This is the answer"

    @recline.command(name="test")
    async def test_coro():  # pylint: disable=unused-variable
        return test_result

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    thread.start()
    thread.background()
    # wait until it is complete
    while thread.is_alive():
        pass
    assert thread.result == test_result


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_stop():
    """Verify that we can kill a long running command"""

    i_was_stopped = False
    i_was_started = False

    @recline.command(name="test")
    async def test_coro():  # pylint: disable=unused-variable
        nonlocal i_was_stopped, i_was_started
        try:
            while True:
                i_was_started = True
                await asyncio.sleep(0.001)
        except asyncio.CancelledError:
            i_was_stopped = True

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    job_pid = thread.job_pid
    thread.start()
    # wait until it is started
    while not i_was_started:
        pass
    thread.stop()
    # wait until it is stopped
    while thread.is_alive():
        pass
    assert i_was_stopped
    assert job_pid not in recline.JOBS


@pytest.mark.usefixtures("clean_jobs")
def test_async_command_exception():
    """Verify that an exception thrown in the background thread is raised to the
    foreground thread when it is foregrounded
    """

    test_result = "This is the exception"

    @recline.command(name="test")
    async def test_coro():  # pylint: disable=unused-variable
        raise RuntimeError(test_result)

    thread = AsyncCommand(recline.commands.COMMAND_REGISTRY["test"])
    job_pid = thread.job_pid
    assert recline.JOBS[job_pid] == thread
    assert recline.NEXT_JOB_PID == job_pid + 1
    thread.start()
    with pytest.raises(RuntimeError, match=test_result):
        assert thread.foreground() == test_result
    assert job_pid not in recline.JOBS
