"""
This module contains a table formatter for CLI output. The table formatter expects
output to be an iterable of dictionary-like objects. For example, if a CLI command
returned something like:

[{'foo': 'bar', 'count': 1}, {'foo': 'baz', 'count': 2}]

Then the table formatter would print this to the screen:

+-----+-------+
| Foo | Count |
+-----+-------+
| bar | 1     |
| baz | 2     |
+-----+-------+
"""

from collections import OrderedDict

from recline.formatters.output_formatter import OutputFormatter


class TableFormat(OutputFormatter):  # pylint: disable=too-few-public-methods
    """A TableFormat object can be used as the return type for a CLI command. When
    specified, the returned value from the CLI command is assumed to be an interable
    of dictionary-like objects. All of the objects are assumed to be homogenous
    with respsect to their keys. It will print out a table representing the data.
    """

    def format_output(self, results):
        """If there are no results given to us, print a message, otherwise print
        a table with a row for each record in the results.
        """

        if not results:
            print('No records')
            return

        columns = list(results[0].keys())
        data = []
        for result in results:
            data.append(list(result.values()))
        self._print_table(columns, data)

    def _print_table(self, headers, data):  # pylint: disable=no-self-use
        """Iterate the data and print lines for the headers and the cells"""

        col_data = OrderedDict()
        row_data = []
        col_widths = [0] * len(headers)
        heading_index = 0
        for heading in headers:
            # longest piece of data for each column
            longest = len(heading)
            for row in data:
                if len(str(row[heading_index])) > longest:
                    longest = len(str(row[heading_index]))

            col_widths[heading_index] = longest
            heading_index += 1
            col_data[heading_index] = (heading, longest)

        for row in data:
            row_dict = OrderedDict()
            heading_index = 0
            for cell in row:
                row_dict[heading_index] = (cell, col_widths[heading_index])
                heading_index += 1
            row_data.append(row_dict)

        _print_border(col_data)
        _print_data_line(col_data, headers=True)
        _print_border(col_data)

        for row in row_data:
            _print_data_line(row)

        _print_border(col_data)


def _print_border(col_data):
    """Print a top or bottom border on the table depending on its width"""

    for _, width in col_data.values():
        print('+', end='')
        print('-' * (width + 2), end='')
    print('+')


def _print_data_line(col_data, headers=False):
    """Print a line of data including the cell borders"""

    for _, (data, width) in col_data.items():
        if headers:
            data = str(data).title().replace('_', ' ')
        print('| %s' % data, end='')
        print(' ' * (width - len(str(data)) + 1), end='')
    print('|')
