"""
Original © NetApp 2024

A test module for the recline.formatters module
"""

from collections import OrderedDict

import pytest

from recline.formatters.table_formatter import TableFormat


@pytest.mark.parametrize('command_results,expected_table', [
    ([], "No records\n"),
    (
        [OrderedDict([('foo', 'bar'), ('baz', 'bleep')])],
        "+-----+-------+\n"
        "| Foo | Baz   |\n"
        "+-----+-------+\n"
        "| bar | bleep |\n"
        "+-----+-------+\n",
    ),
    (
        [
            OrderedDict([
                ('foo_su', 'bar'), ('baz', 'bleep'),
            ]),
            OrderedDict([
                ('foo_su', 'bar2'), ('baz', 'bleep2'),
            ]),
        ],
        "+--------+--------+\n"
        "| Foo Su | Baz    |\n"
        "+--------+--------+\n"
        "| bar    | bleep  |\n"
        "| bar2   | bleep2 |\n"
        "+--------+--------+\n",
    ),
])
def test_table_format(command_results, expected_table, capsys):
    """Verify that our formatter gives the results we expect depending on the input"""

    TableFormat().format_output(command_results)
    captured = capsys.readouterr()
    assert captured.out == expected_table
