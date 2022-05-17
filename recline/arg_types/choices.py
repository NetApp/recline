"""
A Choices type allows the CLI command writer to specify a static list of choices
for a parameter. Once the body of the function is invoked, it is guaranteed that
the validation was done on the parameter to make sure it matched one.

@recline.command(name="cake make")
def make_cake(flavor: Choices.define(["chocolate", "vanilla", "marble"])) -> None:
    # We can assume flavor is one of the choices in the body of the function
"""

from typing import Callable, List, Union

from recline.arg_types.recline_type import ReclineType
from recline.arg_types.recline_type_error import ReclineTypeError


class Choices(ReclineType):
    """The Choices type validates the user input according to a list of possible choices"""

    @staticmethod
    def define(
            available_choices: Union[List, Callable], cache_choices: bool = False,
            inexact: bool = False, data_type=str,
        ) -> "Choices":
        """A `recline.commands.types.Choices` is a way to assert that an argument
        is one of a predefined list.

        Prior to being passed to your command, the argument will be compared to
        the list of defined choices. If it does not match one, an error will be
        printed.

        Args:
            available_choices: The list of allowable values for the argument or
                a callable that will return a list.
            cache_choices: If the available_choices argument was a callable, by
                default it will be called each time the list of choices needs to
                be rendered. But if that callable is expensive, that may not be
                desirable. In that case, passing cache_choices as True will call
                the available_choices function only once to get the list and save
                the result.
            inexact: If set to True, allow the value being validated to contain
                the "*", "|", or ".." query characters. If these characters are
                present, then no validation will be done on the value (and validation
                is assumed to be done on whatever the command is calling)
            data_type: The type of data that represents this argument
        """

        class _Choices(Choices):
            def __new__(cls):
                instance = super().__new__(cls)
                cls.available_choices = available_choices
                if isinstance(available_choices, list):
                    cls.metavar = f"<{'|'.join(available_choices)}>"
                return instance

            def validate(self, arg):
                if inexact:
                    return arg
                current_choices = self.choices(eager=True)
                if arg not in current_choices:
                    raise ReclineTypeError(
                        f"\"{arg}\" must be one of {', '.join(current_choices)}."
                    )
                try:
                    return data_type(arg)
                except Exception:  # pylint: disable=broad-except
                    raise ReclineTypeError(f'Unable to convert "{arg}" to type {data_type}')

            def choices(self, eager=False):
                if hasattr(self.__class__, '_cached_choices'):
                    return self.__class__._cached_choices  # pylint: disable=protected-access

                # don't call the completer function unless we're sure we want to
                if not eager and not isinstance(available_choices, list):
                    return None

                current_choices = self.__class__.available_choices
                try:
                    current_choices = self.__class__.available_choices()
                except TypeError:
                    pass

                current_choices = [str(c) for c in current_choices]
                if cache_choices:
                    self.__class__._cached_choices = current_choices  # pylint: disable=protected-access
                self.__class__.metavar = f"<{'|'.join(current_choices)}>"
                return current_choices

            def completer(self, *args, **kwargs):
                return self.choices(eager=True)

        return _Choices
