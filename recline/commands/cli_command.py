"""
This module contains the definition of a CLICommand object. This is the main
driver of the recline library. Essentially, a CLICommand takes as input a wrapped
function and parses the args and docstring so that when called from the REPL, the
command can be used as prescribed or the help information can be queried.
"""

import argparse
from functools import wraps, partial
import inspect
import io
import json
import logging
from typing import Callable, List, Union

from recline import commands
from recline.arg_types.recline_type import ReclineType, UniqueParam
from recline.arg_types.positional import Positional
from recline.arg_types.flag import Flag
from recline.arg_types.remainder import Remainder
from recline.formatters.output_formatter import OutputFormatter
from recline.vendor import docstring_parser


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


class CLICommand:  # pylint: disable=too-many-instance-attributes
    """This is the implementation of a @recline.command. It sets up all of the
    parameter validation, help text generation, and return output formatting for
    commands defined in the application.
    """

    # pylint: disable=too-many-arguments,bad-continuation
    def __init__(
        self, func,
        name=None,
        group=None,
        is_alias=False,
        hidden=False,
        is_async=False,
    ):
        self.func = func
        self.name = name if name else func.__name__
        self.is_alias = is_alias
        self.group = group
        self.is_async = is_async
        self._hidden = hidden

        signature = inspect.signature(func)
        parameters = signature.parameters
        self.required_args = [
            p for p in parameters.values()
            if p.default == inspect.Parameter.empty
        ]
        self.optional_args = [
            p for p in parameters.values()
            if p.default != inspect.Parameter.empty
        ]
        self.docstring = docstring_parser.parse(self.func.__doc__)

        return_type = signature.return_annotation
        if return_type and issubclass(return_type, OutputFormatter):
            self.output_formatter = return_type()
        else:
            self.output_formatter = None
        self.parser = self._create_parser()

    def __str__(self):
        return (
            '%s(%s, *, %s)' %
            (
                self.name, ', '.join([p.name for p in self.required_args]),
                ', '.join(['%s=%s' % (p.name, p.default) for p in self.optional_args]),
            )
        )

    @property
    def hidden(self):
        """A command is hidden if it is either statically declared to be or it
        was provided with a fuction to determine if it should currently be hidden
        """

        if isinstance(self._hidden, bool):
            return self._hidden
        return self._hidden()

    def _create_parser(self):
        parser = argparse.ArgumentParser(
            add_help=False,
            description=(
                '%s\n\n%s' %
                (self.docstring.short_description, self.docstring.long_description)
            )
        )
        parser.add_argument('-help', help=argparse.SUPPRESS, action=self.print_help())

        if self.is_async:
            parser.add_argument(
                '-background', help="Start this command in the background",
                action="store_true",
            )

        arg_specs = []
        for arg in self.required_args:
            arg_specs.append(self._get_arg_spec(arg, True))
        for arg in self.optional_args:
            arg_specs.append(self._get_arg_spec(arg, False))

        for spec in arg_specs:
            arg = spec[2]
            action = parser.add_argument(*spec[0], **spec[1])
            action.completer = lambda *x, **y: [None]
            annotation_type = get_annotation_type(arg)
            if issubclass(annotation_type, ReclineType):
                if inspect.isclass(arg.annotation):
                    type_instance = arg.annotation()
                action.completer = type_instance.completer
            elif getattr(action, 'choices', None) is not None:
                choices = action.choices[:]
                action.completer = lambda *x, **y: choices  # pylint: disable=cell-var-from-loop

        return parser

    def _get_arg_spec(self, arg, required):
        spec_args = ['-%s' % arg.name]
        spec_kwargs = {
            'action': self.get_arg_action(arg),
            'help': self.get_arg_description(arg),
            'metavar': self.get_arg_metavar(arg),
            'required': required,
        }

        if arg.default != inspect.Parameter.empty:
            spec_kwargs['default'] = arg.default

        def _recline_type_annotation_handler(arg_annotation, nargs=None):
            nonlocal spec_args, spec_kwargs, arg

            if inspect.isclass(arg_annotation):
                type_instance = arg_annotation()
            type_instance.arg_name = arg.name
            spec_kwargs['type'] = type_instance.validate
            choices = type_instance.choices()
            if choices is not None:
                spec_kwargs['choices'] = choices
            spec_kwargs['nargs'] = nargs or type_instance.nargs()

            special_nargs = (
                spec_kwargs['nargs'] == argparse.REMAINDER or
                isinstance(type_instance, Positional)
            )
            if special_nargs:
                del spec_kwargs['required']
                spec_args = [arg.name]
                if isinstance(type_instance, Positional) and arg.default is not None:
                    spec_kwargs['nargs'] = '?'
            if isinstance(type_instance, Flag):
                del spec_kwargs['metavar']
                del spec_kwargs['type']
                del spec_kwargs['nargs']

        if arg.annotation:
            annotation_type = get_annotation_type(arg)
            if issubclass(annotation_type, List):
                if issubclass(arg.annotation.__args__[0], ReclineType):
                    _recline_type_annotation_handler(arg.annotation.__args__[0], '+')
                else:
                    spec_kwargs['nargs'] = '+'
            if issubclass(annotation_type, bool):
                spec_kwargs['choices'] = [True, False]
                spec_kwargs['type'] = lambda val: val.lower() == 'true'
            if issubclass(annotation_type, int) and not issubclass(annotation_type, bool):
                spec_kwargs['type'] = int
            if issubclass(annotation_type, dict):
                spec_kwargs['type'] = json.loads
            if issubclass(annotation_type, ReclineType):
                _recline_type_annotation_handler(annotation_type)

        return spec_args, spec_kwargs, arg

    def get_arg_action(self, arg):  #pylint: disable=no-self-use
        """By default, arguments will be verified as unique. However, if a custom
        type defines an action that should be taken when parsing the command line,
        that action will be used instead.
        """

        action = UniqueParam
        if not arg.annotation:
            return action

        annotation_type = get_annotation_type(arg)
        if issubclass(annotation_type, ReclineType):
            return annotation_type.action
        return action

    def get_arg_metavar(self, arg):  #pylint: disable=no-self-use,too-many-return-statements
        """By default, the metavar for an argument is the same as the name of that
        argument (and enclosed in <>). But there are many situations with custom
        types where the metavar will be defined by the type and should be taken
        from the type.
        """

        basic = '<%s>' % arg.name
        if not arg.annotation:
            return basic

        annotation_type = get_annotation_type(arg)

        if issubclass(annotation_type, Positional):
            return basic
        if issubclass(annotation_type, ReclineType):
            return arg.annotation.metavar
        if issubclass(annotation_type, List):
            return '<%s> [%s ...]' % (arg.name, arg.name)
        if issubclass(annotation_type, bool):
            return '<true|false>'
        if issubclass(annotation_type, int):
            return '<int>'
        return basic

    def get_arg_description(self, arg, indent=0):
        """Get the descrption of the arg from the parsed docstring if we can find
        one. Otherwise, the description will be blank.
        """

        for doc_param in self.docstring.params:
            if doc_param.arg_name == arg.name:
                if indent is None:
                    return doc_param.description.replace('\n', ' ')
                return doc_param.description.replace('\n', '\n' + ' ' * indent)
        return ''

    def get_arg_help(self, arg, indent=True):
        """Get a line of help text for an argument including the name, metavar,
        and description of the argument.
        """

        annotation_type = get_annotation_type(arg)
        positional = '' if issubclass(annotation_type, (Positional, Remainder)) else '-'
        name_meta = '  %s%s %s ' % (positional, arg.name, self.get_arg_metavar(arg))
        if issubclass(annotation_type, Positional):
            name_meta = '  %s ' % self.get_arg_metavar(arg)
        if issubclass(annotation_type, Flag):
            name_meta = '  %s%s ' % (positional, arg.name)
        indent = len(name_meta) if indent else None
        arg_help = name_meta
        arg_description = self.get_arg_description(arg, indent=indent)
        if arg_description:
            arg_help += arg_description
        if arg.default != inspect.Parameter.empty and not issubclass(annotation_type, Flag):
            default_val = arg.default
            if isinstance(arg.default, bool):
                default_val = str(arg.default).lower()
            arg_help += '\n    Default: %s' % default_val
        return arg_help

    def get_command_help(self):
        """Get a block of help text for the command including all of its arguments
        as well as a short description of the command.
        """

        help_text = []
        if self.docstring.short_description:
            help_text.append(self.docstring.short_description)
        if self.required_args or self.optional_args:
            help_text.append('')
        if self.required_args:
            help_text.append('Required arguments:')
            for arg in self.required_args:
                help_text.append(self.get_arg_help(arg))
            if self.optional_args:
                help_text.append('')
        if self.optional_args:
            help_text.append('Optional arguments:')
            for arg in self.optional_args:
                help_text.append(self.get_arg_help(arg))

        return '\n'.join(help_text)

    def get_command_usage(self):
        """Get the short usage spec for the command"""

        str_file = io.StringIO()
        self.parser.print_usage(file=str_file)
        usage = str_file.getvalue()
        # argparse gives us a few pieces we need to replace
        usage = ' '.join(usage.split(' ')[2:])
        return self.name + ' ' + usage.strip()

    def print_help(outer_self):  # pylint: disable=no-self-argument
        """If the -help argument is passed to the command, then this method will
        print out the help for that command instead of the builtin argparse help printer.
        """

        class HelpAction(argparse.Action):  # pylint: disable=too-few-public-methods
            """This is a custom help action which implements the argparse action
            protocol.
            """

            # pylint: disable=bad-continuation
            def __init__(
                self,
                option_strings,
                dest=argparse.SUPPRESS,
                default=argparse.SUPPRESS,
                help=None  # pylint: disable=redefined-builtin
            ):
                super().__init__(option_strings, dest=dest, default=default, nargs=0, help=help)
            def __call__(self, parser, namespace, values, option_string=None):
                print(outer_self.get_command_help())
                parser.exit()
        return HelpAction


# pylint: disable=too-many-arguments,bad-continuation
def command(
    func=None,
    name: str = None,
    group: str = None,
    aliases: List[str] = None,
    atstart: bool = False,
    atexit: bool = False,
    hidden: Union[Callable[[], bool], bool] = False
):
    """Wrapping a function with this registers it with the recline library and
    exposes it as a command the user of the application can call.

    The name of the command will match the name of the function that is being
    wrapped. The arguments of the command will match the arguments that the
    function accepts. Any arugments that are required by the function will be
    required arguments for the command. Any arguments that are optional (listed
    as keyword arguments) will be optional for the command.

    Args:
        name: If the command name shouldn't inherit the function name, it can be
            defined here. This can be especially useful if the command name has
            spaces in it.
        group: If certain commands should be logically grouped together, they
            should share the same group name.
        aliases: An optional list of other names that will map back to the same
            function. For example, if the function was called 'exit', a list of
            aliases might be ['quit', 'q'].
        atstart: If set to True, this command will run before the main REPL is
            available for processing other commands. If this command fails, the
            REPL won't become available.
        atexit: Before exiting the program, this command will be run and can be
            used to clean up any resources. This command should always take 0
            arguments.
        hidden: If the command is hidden, then it will not be shown in the help
            output or available for autocompletion. It will still be executable
            by the user if they type it out. This can be either a function which
            evaluates to True or False, or just a constant True or False.
    """


    if func is None:
        return partial(
            command, name=name, group=group, aliases=aliases, atstart=atstart,
            atexit=atexit, hidden=hidden,
        )

    is_async = inspect.iscoroutinefunction(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    _register(wrapper, name, group, aliases, atstart, atexit, hidden, is_async)
    return wrapper


# pylint: disable=too-many-arguments
def _register(func, name, group, aliases, atstart, atexit, hidden, is_async):
    if atstart:
        if commands.START_COMMAND:
            raise RuntimeError('A start command is already defined: %s' % func)
        commands.START_COMMAND = CLICommand(func)
        return
    if atexit:
        if commands.EXIT_COMMAND:
            raise RuntimeError('An exit command is already defined: %s' % func)
        commands.EXIT_COMMAND = CLICommand(func)
        return

    command_name = func.__name__
    if name is not None:
        command_name = name

    if not aliases:
        aliases = [command_name]
    else:
        aliases.insert(0, command_name)

    for index, alias in enumerate(aliases):
        is_alias = index > 0
        commands.COMMAND_REGISTRY[alias] = CLICommand(
            func, name=alias, group=group, is_alias=is_alias, hidden=hidden,
            is_async=is_async,
        )
        if not is_alias:
            LOGGER.debug('Registered %s', commands.COMMAND_REGISTRY[alias])
        else:
            LOGGER.debug('Aliased %s to %s', alias, command_name)


def get_annotation_type(arg):
    """Python 3.7 explicitly broke the issubclass checking on the typing module
    https://bugs.python.org/issue34568
    """

    return getattr(arg.annotation, '__origin__', arg.annotation)
