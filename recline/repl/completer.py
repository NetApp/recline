"""
Original © NetApp 2024

This module implements a readline completer for completing command names as well
as argument names and values.
"""

import argcomplete
import argparse
import re
import readline
import sys

import recline
from recline.arg_types.recline_type import UniqueParam


def match_command_hook(substitution, matches, *_):
    """ Print a list of completion choices in columns and reprint the prompt """

    end = readline.get_endidx()
    current_line = readline.get_line_buffer()

    # back up the substitution string to the last full word in case of
    # partial matching
    substitution = ' '.join(substitution.split(' ')[:-1])
    completions = []
    for match in matches:
        subbed_match = match.replace(substitution, '').strip()
        if subbed_match:
            completions.append(subbed_match)

    sys.stdout.write(
        '\n%s\n%s%s\r%s%s' % (
            print_columns(completions), recline.PROMPT, current_line,
            recline.PROMPT, current_line[:end],
        )
    )


def print_columns(objects, cols=3, gap=2):
    """ Print a list of items in rows and columns """

    # if the list is empty, do nothing
    if not objects:
        return ""

    # make sure we have a string for each item in the list
    str_list = [str(x) for x in objects]

    # can't have more columns than items
    if cols > len(str_list):
        cols = len(str_list)

    max_length = max([len(x) for x in str_list])

    # get a list of lists which each represent a row in the output
    row_list = [str_list[i:i+cols] for i in range(0, len(str_list), cols)]

    # join together each row in the output with a newline
    # left justify each item in the list according to the longest item
    output = '\n'.join([
        ''.join([x.ljust(max_length + gap) for x in row_item])
        for row_item in row_list
    ])

    return output


class CommandCompleter:
    """A completer object that can be used to get the possible next choices for
    the user's current input. Used with readline's set_completer() function.
    """

    def __init__(self, commands):
        self.options = sorted(commands.keys())
        self.commands = commands
        self.matches = self.options[:]

    @staticmethod
    def get_command_name(text, options, exact=True):
        """ The text contains a complete command if there is 1 and only 1 command
            which contains the text's prefix
        """

        if exact and text in options:
            return text

        pieces = text.split(' ')
        i = len(pieces)
        command_name = None
        possible_match = None
        while i > 0:
            prefix = ' '.join(pieces[:i])
            possibles = [x for x in options if x.startswith(prefix)]
            if len(possibles) == 1:
                command_name = prefix
                possible_match = possibles[0]
                break
            if len(possibles) > 1:
                # This block covers the case where there are two commands with
                # the same prefix and the user has started typing args
                # Something like this:
                # possibles = ["deploy", "deploy status"]
                # text = "deploy 5"

                # walk each word of each possible
                # for each word, compare it to each word of the text
                # if the possible word starts with the matching text word, then
                # it is still a possible. Otherwise, it's not possible anymore
                still_possible = []
                for possible in possibles:
                    for index, possible_word in enumerate(possible.split(' ')):
                        if index > len(pieces) - 1:
                            continue
                        if not possible_word == pieces[index]:
                            break
                    else:
                        still_possible.append(possible)
                if len(still_possible) == 1:
                    command_name = still_possible[0]
                    possible_match = still_possible[0]
                    break

            i -= 1

        if command_name is not None and command_name == possible_match.strip():
            return command_name
        return None

    def _get_command_matches(self, command_str, text):
        """ Get the possible matches from a command by calling its completer """

        parser = self.commands[command_str].completer_parser
        completer = argcomplete.CompletionFinder(
            parser, always_complete_options='long'
        )
        matches = []
        state = 0
        for match in iter(lambda: completer.rl_complete(text, state), None):
            if not _already_added_match(parser, match, text):
                matches.append(match)
            state += 1

        return sorted(matches)

    def _parse_around_booleans(self, text):  # pylint: disable=no-self-use
        """In order to get completions for commands which might be part of a
        complex command line, we need to discard the parts of the complex command
        that we're not currently working on.

        For example, if the user was working on this sort of statement:

            my command -arg 1 && my other command -type ┋ ; my third command

        The user's cursor is where you see the ┋ and they have pressed tab. We
        need to know to only consider the "my other command -type " part of the
        line and nothing else
        """

        # when readline gives us the text, it only gives us the text up until
        # our cursor so we don't need to worry about anything after it
        right_hand_side = text.split("&&")[-1].split("||")[-1].split(";")[-1]
        left_hand_side = text[::-1].replace(right_hand_side[::-1], '', 1)[::-1]
        return left_hand_side, right_hand_side.lstrip()

    def completer(self, text, state):
        """To be used with readline's set_completer() function"""

        response = None
        prefix, text = self._parse_around_booleans(text)
        if state == 0:
            # if the text on the line already contains a complete command, we'll
            # need to get completions from that command instead
            command_name = self.get_command_name(text, self.options, exact=False)
            if command_name:
                self.matches = self._get_command_matches(command_name, text)
                if not self.matches and command_name == text:
                    self.matches.append(command_name + ' ')
            # This is the first time for this text, so build a match list
            elif text:
                self.matches = [x for x in self.options if x.startswith(text.strip())]
            else:
                self.matches = self.options[:]

        # Return the state'th item from the match list, if we have that many
        try:
            response = self.matches[state]
        except Exception:  # pylint: disable=broad-except
            return None

        current_line = readline.get_line_buffer()
        response = prefix + ' ' + response.rstrip()
        if not current_line.replace(prefix, '').lstrip().replace(text, '').startswith(' '):
            response += ' '
        return response.lstrip()


def _already_added_match(parser, match, text):
    """ Return True if the match given is not already specified in the text
        or if it is not a unique action and can be specified multiple times.
    """

    # pylint: disable=protected-access

    match = match.strip().split(' ')[-1]
    match_already_added = False
    unique_classes = [UniqueParam, argparse._StoreTrueAction, argparse._StoreFalseAction]

    for action in parser._actions:
        if match not in action.option_strings:
            continue

        action_is_unique = action._orig_class in unique_classes
        action_is_present = re.search(f' {match}', text)

        if action_is_unique and action_is_present:
            match_already_added = True
            break

    return match_already_added
