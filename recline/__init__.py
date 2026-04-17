"""
Original © NetApp 2024
"""

PROGRAM_NAME = None
PROMPT = '> '
NEXT_JOB_PID = 1
JOBS = {}

from recline.commands.cli_command import command  # noqa: E402
from recline.repl.shell import relax  # noqa: E402

__all__ = ['PROGRAM_NAME', 'PROMPT', 'command', 'relax']
