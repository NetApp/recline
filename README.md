![](https://github.com/NetApp/cliche/workflows/build/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/NetApp/cliche/branch/master/graph/badge.svg?token=QPHL12QH4N)](https://codecov.io/gh/NetApp/cliche)
[![Gitter](https://badges.gitter.im/netapp-cliche/community.svg)](https://gitter.im/netapp-cliche/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

# cliche

Writing argparse-based command line applications can become tedious, repetitive,
and clichéd. Let this library free you from that burden.

This library helps you quickly implement an interactive command-based application in Python.

## Documentation First
We all know that writing documentation is very important and yet it can easily become
and afterthought or a nice to have if we're not diligent. This is often because it
means duplicating a piece of your implementation in words, effectively writing the
same thing twice. Cliche strives to deduplicate this work by taking a documentation
first attitude where your documentation _becomes_ the implementation without additional
work from you.

## Interactive

The default mode is to run a REPL interface where a prompt is given to the user, the
user types one of the available commands, the application processes it, displays the
result, and then control is returned to the user once more.

But if your user isn't expected to or doesn't always want to run multiple commands,
you also get a more traditional command-line interface for free.

## Command-based

The application will be command based. Each command will have one or more words
that identify the command. It may also have one or more arugments that augment or
vary the action that command will take.

## Batteries included

While the library is designed to be easy to implement for simple or small applications,
it also comes with full power features for larger use cases including:

* Tab completion
* Input verification
* Output formatting
* Debugger integration

# Before getting started

Some things to consider and prepare before you can use this library.

## Software requirements

```
1. Python 3.5 or later
```

## Installing and importing the library

You can install the package using the pip utility:

```
pip install cliche
```

You can then import the library into your application:

```python
import cliche
```

# Quick Start

After installing the package, you can get started with a few lines in `hello.py`:

```python
import cliche

@cliche.command
def hello(name: str = None) -> None:
    """A basic hello world

    You can greet just about anybody with this command if they give you their name!

    Args:
        name: If a name is provided, the greeting will be more personal
    """
    response = "I'm at your command"
    if name:
        response += ", %s" % name
    print(response)

cliche.run()
```

## Interactive mode

The default mode when a cliche applciation is run is an interactive style. Running
our above `hello.py` results in the following output:

```
$ python hello.py
> help
Available Commands:

hello - A basic hello world You can greet just about anybody with this command if

Built-in Commands
-----------------
exit - Exit the application
help - Display a list of available commands and their short description
man - Display the full man page for a given command
> hello ?
A basic hello world You can greet just about anybody with this command if

Optional arguments:
  -name <name> If a name is provided, the greeting will be more personal
    Default: None
> hello
I'm at your command
> hello -name Dave
I'm at your command, Dave
> exit
$
```

## Non-interactive mode

If you would like to use the application as part of a larger script, it is much
easier to do in a non-interactive way. This is also possible using cliche without
needing to change the application. Here's an example:

```
$ python hello.py -c "hello -name Dave"
I'm at your command, Dave
$
```

See the full documentation for more advanced usages and examples

# Building the package

If you are making and testing changes to cliche itself, the following commands
will be useful to know. This repository makes use of [poetry](https://github.com/python-poetry/poetry)
for configuring a virtual environment and so the commands below will reference
it so that they are run inside of that environment. If you want more information
about Poetry, then you can view the documentation [here](https://python-poetry.org/docs/basic-usage/)

## Setting up your environment

This command will create a new virtual environment and install the dependencies
in it.

```
$ poetry install
```

## Testing changes

```
$ poetry run pytest --cov=cliche tests
```

## Building the package

```
$ poetry build
```

## Building the docs

```
$ poetry run sphinx-apidoc -H "API Reference" -o docs/api_reference cliche
$ poetry run sphinx-build -b html docs build/html
```
