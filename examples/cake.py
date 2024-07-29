"""
Original © NetApp 2024

A simple application for making and listing the cakes we have
"""


from collections import OrderedDict
from time import sleep

import recline
from recline.arg_types.choices import Choices
from recline.arg_types.ranged_int import RangedInt
from recline.formatters.table_formatter import TableFormat


CAKES = []


# pylint: disable=bad-continuation
@recline.command(name="cake make")
def make_cake(
    layers: RangedInt.define(min=2, max=10),
    flavor: Choices.define(["chocolate", "vanilla", "marble"]),
) -> None:
    """Make a cake with the specified number of layers

    Pat-a-cake, pat-a-cake, baker's man.
    Bake me a cake as fast as you can
    Pat it, and prick it, and mark it with "B"
    And put it in the oven for Baby and me!

    Args:
        layers: The number of layers to build the cake from.
        flavor: The flavor of cake to make.

    Examples:
        layer_validation_failure:
            ::> cake make -flavor chocolate -layers 1
            layers: 1 is not an integer in the range {2-10}.
        type_validation_failure:
            ::> cake make -flavor bogus -layers 2
            flavor: "bogus" must be one of chocolate, vanilla, marble.
        success:
            ::> cake make -flavor chocolate -layers 2
            Adding ingredients
            Mixing the batter
            Baking the cake
            Made a 1 layer chocolate cake. Sorry, I burned one layer.
            ::>
    """

    CAKES.append(OrderedDict([("cake layers", layers - 1), ("flavor", flavor)]))
    print("Adding ingredients")
    sleep(2)
    print("Mixing the batter")
    sleep(3)
    print("Baking the cake")
    sleep(5)
    print("Made a %s layer %s cake. Sorry, I burned one layer." % (layers - 1, flavor))


@recline.command(name="cake show")
def show_cake() -> TableFormat:
    """Show all of our completed cake work"""

    return CAKES


recline.relax(history_file=".cake_history.txt", prompt="::> ")
