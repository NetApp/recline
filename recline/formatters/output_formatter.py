"""
This module contains the abstract class that all other output formatters should
inherit from
"""

from abc import ABC, abstractmethod

class OutputFormatter(ABC):  # pylint: disable=too-few-public-methods
    """All output formatters should inherit from this class"""

    @abstractmethod
    def format_output(self, results):
        """The implementation of this method should expect to receive the results
        of a command output and to process them and output them in whatever manner
        is appropriate for the specific formatter.
        """
