"""
A RangedInt type allows the CLI command writer to specify an integer that is only
valid within a certain range. If the user provides a value outside of that range,
then the parameter validation will fail and they will receive an error message.

@recline.command(name="bake cake")
def bake(minutes: RangedInt.define(min=15, max=60)) -> None:
    # If the user tried to bake the cake for less than 15 minutes or more than
    # 60 minutes, then this body wouldn't be called and they would get an error.
"""

from recline.arg_types.recline_type import ReclineType
from recline.arg_types.recline_type_error import ReclineTypeError


class RangedInt(ReclineType):
    """The RangedInt type allows a parameter which is an into to be constrained
    in which values are in the valid range.
    """

    # pylint: disable=bad-continuation
    @staticmethod
    def define(
        min: int = None,  # pylint: disable=redefined-builtin
        max: int = None,  # pylint: disable=redefined-builtin
    ) -> "_RangedInt":
        """A `recline.commands.types.RangedInt` is a way to annotate an integer with
        a min and max value.

        Prior to being passed to your command, the arguments of this type will
        be validated according to the parameters specified. For example, if a
        minimum is given, then the argument must be less than the minimum before
        your command will be called with it.

        Args:
            name: This is the name of the parameter and is required for building
                the help text of the command.
            min: If provided, the user-supplied argument will be validated to be
                and integer >= this value.
                argument will be enforced.
            max: If provided, the user-supplied argument will be validated to be
                and integer <= this value.
        """

        min_val = min
        max_val = max

        class _RangedInt(RangedInt):
            metavar = '<int>'

            range_str = ''
            if min_val is not None and max_val is not None:
                range_str = '{%s-%s}' % (min_val, max_val)
            elif min_val is not None:
                range_str = '{%s-inf}' % min_val
            elif max_val is not None:
                range_str = '{-inf-%s}' % max_val
            metavar = f'<int{range_str}>'

            def validate(self, arg):
                try:
                    int_val = int(arg)
                    if min_val is not None and int_val < min_val:
                        raise ValueError()
                    if max_val is not None and int_val > max_val:
                        raise ValueError()
                    return int_val
                except ValueError:
                    raise ReclineTypeError(
                        f'"{arg}" is not an integer in the range {_RangedInt.range_str}.'
                    )

        return _RangedInt
