"""
Copyright (C) 2020 NetApp Inc.
All rights reserved.
"""

import os
import sys

PROGRAM_NAME = None
PROMPT = '> '
NEXT_JOB_PID = 1
JOBS = {}

from recline.commands.cli_command import command  # pylint: disable=wrong-import-position
from recline.repl.shell import relax  # pylint: disable=wrong-import-position

__all__ = ['PROGRAM_NAME', 'PROMPT', 'command', 'relax']
