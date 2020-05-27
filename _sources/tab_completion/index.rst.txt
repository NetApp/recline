Tab Completion
==============

The library provides generic tab completion functionality. This can either be
automatic (for example, parameters of type ``bool``) or provided by the business
logic of the application. Consider the sample program below:

.. code-block:: Python

    import cliche
    from cliche.arg_types.choices import Choices
    from cliche.formatters.table_formatter import TableFormat

    # A stand-in for a database or some other form of persistence
    ORDERS = {}
    MENU = ['black bean', 'choirizo', 'steak']

    def get_customers():
        return list(ORDERS.keys())

    def get_order_types():
        return [o["type"] for o in ORDERS.values()]

    @cliche.command(name="order burrito")
    def order_burrito(
        customer_name: str,
        type: Choices.define(available_choices=MENU),
        grilled: bool = True,
    ) -> None:
        """Place an order for a delicious burrito

        Arguments:
            cusomter_name: The name of the customer who is ordering
            type: Describes the fillings of the burrito
            grilled: If the burrito should be browned on the grill
        """

        ORDERS[customer_name] = {"type": type, "grilled": grilled}
        print("One order for a %s burrito, coming up!" % type)

    @cliche.command(name="show orders")
    def show_orders(
        customer_name: Choices.define(available_choices=get_customers) = None,
        type: Choices.define(available_choices=get_order_types) = None,
        grilled: bool = None,
    ) -> TableFormat:
        """List all of the orders that match the given query

        Arguments:
            cusomter_name: The name of the customer who made the order
            type: The type of burrito that was ordered
            grilled: List only burritos with this grilling status

        Returns:
            A list of all orders matching the query
        """

        matching_orders = []
        for customer, order in ORDERS.items():
            if customer_name and customer != customer_name:
                continue
            if type and type != order["type"]:
                continue
            if grilled is not None and grilled != order["grilled"]:
                continue
            matching_orders.append({"customer": customer, "type": order["type"], "grilled": order["grilled"]})

        return matching_orders

    cliche.run(prompt="tacos galore> ")

.. note::
    In the examples below, I will put the string ``[Tab]`` in the output to show
    where the ``[Tab]`` key was typed. The characters are not literally displayed
    when running the program.

Command Completion
------------------

The first level of tab completion is command completion. This means that the user
can press the ``[Tab]`` key in order to show the list of commands the matches the
current input on the command line. For example, if there was nothing typed yet, the
program above would display this::

    tacos galore> [Tab]
    ?              debug          exit
    fg             help           man
    order burrito  q              quit
    show orders
    tacos galore>

Here, all of the available commands, including the builtin commands are shown. If
the user started typing the command they wanted to execute and then hit ``[Tab]``,
it might look like this::

    tacos galore> ord[Tab]
    tacos galore> order burrito

Hard to show here, but there would not be two lines on the display. The library
knows that the only command that matches the prefix ``ord`` is ``order burrito``
and completes the rest of the words.

Argument Completion
-------------------

Continuing from the last section, if the user presses ``[Tab]`` immediately,
they will be shown a list of available arguments::

        tacos galore> order burrito [Tab]
        -customer_name  -grilled        -type
        tacos galore> order burrito -

Here, we can see that the list is shown starting on the next line and then the
library reprinted what was already typed and started filling in the common prefix
that all of the arguments have in common (in this case, just a ``-``). If there
had been more of a common prefix, it would have included that as well.

Knowing that they want to fill in the type field, the user types a ``t`` and presses
``[Tab]`` again::

    tacos galore> order burrito -t[Tab]
    tacos galore> order burrito -type

Again, this would not appear on two lines on the display.

Value Completion
----------------

Continuing from the last section, the user wants to complete an order so they
press ``[Tab]`` once more to determine which types are available::

    tacos galore> order burrito -type [Tab]
    black\ bean  choirizo     steak
    tacos galore> order burrito -type ch[Tab]
    tacos galore> order burrito -type chorizo -cust[Tab]
    tacos galore> order burrito -type chorizo -customer_name Suzane
    One order for a choirizo burrito, coming up!
    tacos galore>

After finishing our order, we can see the current orders by again pressing ``[Tab]``
as we navigate the show command::

    tacos galore> sh[Tab]
    tacos galore> show orders [Tab]
    -customer_name  -grilled        -type
    tacos galore> show orders -cu[Tab]
    tacos galore> show orders -customer_name [Tab]
    tacos galore> show orders -customer_name Suzane
    +----------+----------+---------+
    | Customer | Type     | Grilled |
    +----------+----------+---------+
    | Suzane   | choirizo | True    |
    +----------+----------+---------+
    tacos galore>

Since we pressed ``[Tab]`` to find the possible choices for customer name and there
was only one, the library filled it in for us. If there was more than one value
available, it would have showed us choices like this::

    tacos galore> order burrito -type choirizo -customer_name Sue
    One order for a choirizo burrito, coming up!
    tacos galore> show orders -customer_name [Tab]
    Sue     Suzane
    tacos galore> show orders -customer_name Su

We can see that this time, since they share a prefix, the library filled in the
common parts of the name and waits for the user to give more uniqueness.
