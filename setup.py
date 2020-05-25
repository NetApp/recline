"""
Setup/install the cliche library
"""

import os
import setuptools

import cliche

with open("README.md", "r", encoding="utf-8") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name=os.getenv("PACKAGE_NAME", "cliche"),
    version=cliche.__version__,
    author="NetApp",
    author_email="support@netapp.com",
    description="A library for creating interactive (REPL) and non-interactive CLI applications",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    install_requires=[],
    python_requires='>=3.5',
)
