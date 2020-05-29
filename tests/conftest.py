"""
pytest configuration for recline unit tests
"""

import pytest

import recline


@pytest.fixture(scope='function')
def clean_jobs():
    """Make sure the globals are fresh in each test"""

    recline.JOBS = {}
    recline.NEXT_JOB_PID = 1
    recline.commands.COMMAND_REGISTRY = {}
