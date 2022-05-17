# Contributing

When contributing to this repository, you may open a pull request with your proposed changes or bug fix or you may first discuss the change you wish to make via issue,
email, or any other method with the maintainers of this repository.

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Building the package

If you are making and testing changes to recline itself, the following commands
will be useful to know. This repository makes use of [poetry](https://github.com/python-poetry/poetry)
for configuring a virtual environment and so the commands below will reference
it so that they are run inside of that environment. If you want more information
about Poetry, then you can view the documentation (along with installation instructions
for poetry itself) [here](https://python-poetry.org/docs/basic-usage/)

### Setting up your environment

This command will create a new virtual environment and install the dependencies
in it.

```
$ poetry install
```

### Running an example script
```
$ poetry run python examples/cake.py
```

### Testing changes

```
$ poetry run pytest --cov=recline tests
```

### Building the package

```
$ poetry build
```

### Building the docs

```
$ poetry run sphinx-build -b html docs build/html
```

## Filing Issues

If you find a bug or you have a feature request, you can file an issue using the
GitHub [issues](https://github.com/NetApp/recline/issues) system. Please be sure to include as much information as possible about the issue you are facing and your configuration or reproduction steps.

## Creating a Pull Request

After you've made changes and tested that they work using the steps above, you may file a pull request to have your changes merged into the code base. If you are unfamiliar with the process, you can find GitHub's documentation about it [here](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request)
