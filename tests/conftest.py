"""
pytest configuration for cliche unit tests
"""

import pytest

import cliche


@pytest.fixture(scope='function')
def clean_jobs():
    """Make sure the globals are fresh in each test"""

    cliche.JOBS = {}
    cliche.NEXT_JOB_PID = 1
    cliche.commands.COMMAND_REGISTRY = {}
