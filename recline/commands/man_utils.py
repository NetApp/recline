"""
This module holds some utility functions used as part of the man command to format
text from CLI commands into consistent man pages that respond to the terminal
width.
"""

import curses

from recline.arg_types.positional import Positional
from recline.arg_types.remainder import Remainder
from recline.commands.cli_command import get_annotation_type


def wrapped_string(text, screen_width, prefix=0):
    """This function will take a string and make sure it can fit within the
    given screen_width.

    If the string is too long to fit, it will be broken on word boundaries
    (specifically the ' ' character) if it can or the word will be split with
    a '-' character and the second half moved to the next line.

    If a prefix is given, the line(s) will be prefixed with that many ' '
    characters, including any wrapped lines.

    If the given string includes embedded newline characters, then each line
    will be evaluated according to the rules above including breaking on word
    boundaries and injecting a prefix.
    """

    if not text:
        return ''
    new_text = ''

    # if we have multiple paragraphs, then wrap each one as if it were a single line
    lines = text.split('\n')
    if len(lines) > 1:
        for index, line in enumerate(lines):
            if index > 0:
                new_text += ' ' * prefix
            new_text += wrapped_string(line, screen_width, prefix=prefix) + '\n'
        return new_text.rstrip()

    if len(text) + prefix < screen_width:
        return text
    words = text.split(' ')
    current_line = ''
    for word in words:
        if prefix + len(current_line) + len(word) + 1 < screen_width:
            # if word fits on line, just add it
            current_line += word + ' '
        else:
            space_left = screen_width - (prefix + len(current_line))
            if space_left < 3 or len(word) - space_left < 3:
                # if not much room, move whole word to the next line
                new_text += f'{current_line.rstrip()}\n'
                current_line = f"{' ' * prefix}{word} "
            else:
                # split the word across lines with a hyphen
                current_line += word[:space_left - 1] + '-'
                new_text += current_line.rstrip() + "\n"
                current_line = ' ' * prefix + word[space_left - 1:] + ' '
    new_text += current_line.rstrip()
    return new_text


def generate_help_text(screen_width, command_class):
    """Generates lines of help text which are formatted using the curses library.
    The final document resembles a typical Linux-style manpage. See here:
    https://www.tldp.org/HOWTO/Man-Page/q3.html
    """

    # generate styled man page, one section at a time
    help_text = []
    indent = '     '

    # command name and short description
    help_text.append(('NAME\n', curses.A_BOLD))
    help_text.append((indent,))
    help_text.append((command_class.name, curses.A_BOLD))
    help_text.append((' -- ',))
    description = wrapped_string(
        command_class.docstring.short_description, screen_width,
        prefix=(len(command_class.name) + len(indent) + 4),
    )
    for line in description.split('\n'):
        help_text.append((f'{line}\n',))
    help_text.append(('\n',))

    # command usage details
    help_text.append(('SYNOPSIS\n', curses.A_BOLD))
    help_text.append((indent,))
    description = wrapped_string(
        command_class.get_command_usage(), screen_width, prefix=len(indent),
    )
    for line in description.split('\n'):
        help_text.append((f'{line}\n',))
    help_text.append(('\n',))

    # command detailed description
    if command_class.docstring.long_description:
        help_text.append(('DESCRIPTION\n', curses.A_BOLD))
        help_text.append((indent,))
        description = wrapped_string(
            command_class.docstring.long_description, screen_width,
            prefix=len(indent),
        )
        for line in description.split('\n'):
            help_text.append((f'{line}\n',))
        help_text.append(('\n',))

    # each command parameter with description, constraints, and defaults
    if command_class.docstring.params:
        def print_arg(arg):
            meta = command_class.get_arg_metavar(arg)
            description = command_class.get_arg_description(arg, indent=None)
            annotation_type = get_annotation_type(arg)
            positional = '' if issubclass(annotation_type, (Remainder, Positional)) else '-'
            arg_name = '' if issubclass(annotation_type, Positional) else f'{arg.name} '
            prefix = f'{indent}  {positional}{arg_name}{meta} '
            help_text.append((prefix,))
            description = wrapped_string(
                description, screen_width, prefix=len(prefix)
            )
            for line in description.split('\n'):
                help_text.append((f'{line}\n',))
            help_text.append(('\n'),)
        help_text.append(('OPTIONS\n', curses.A_BOLD))
        if command_class.required_args:
            help_text.append((indent,))
            help_text.append(('Required:\n', curses.A_UNDERLINE))
        for arg in command_class.required_args:
            print_arg(arg)
        if command_class.optional_args:
            help_text.append((indent,))
            help_text.append(('Optional:\n', curses.A_UNDERLINE))
        for arg in command_class.optional_args:
            print_arg(arg)

    # each command example
    if command_class.docstring.examples:
        help_text.append(('EXAMPLES\n', curses.A_BOLD))
        for example in command_class.docstring.examples:
            prefix = indent + '  '
            help_text.append((indent,))
            help_text.append((f'{example.name}:', curses.A_UNDERLINE))
            help_text.append((f'\n{prefix}',))
            description = wrapped_string(
                example.description, screen_width, prefix=len(prefix),
            )
            for line in description.split('\n'):
                help_text.append((f'{line}\n',))

    return help_text
