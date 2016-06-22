#!/usr/bin/env python

from __future__ import print_function

import os
from setuptools import setup
import textwrap


NAME = 'iris_grib'
DIR = os.path.abspath(os.path.dirname(__file__))


LONG_DESCRIPTION = textwrap.dedent("""
    Iris loading of GRIB files
    ==========================

    With this package, iris is able to load GRIB files:

    ```
    my_data = iris.load(path_to_grib_file)
    ```
    """)


def extract_packages():
    packages = []
    root = os.path.join(DIR, 'lib', NAME)
    offset = len(os.path.dirname(root)) + 1
    for dpath, _, _ in os.walk(root):
        if os.path.exists(os.path.join(dpath, '__init__.py')):
            package = dpath[offset:].replace(os.path.sep, '.')
            packages.append(package)
    return packages


def extract_version():
    version = None
    fname = os.path.join(DIR, 'lib', NAME, '__init__.py')
    with open(fname) as fd:
        for line in fd:
            if (line.startswith('__version__')):
                _, version = line.split('=')
                version = version.strip()[1:-1]  # Remove quotation characters
                break
    return version


setup_args = dict(
    name             = NAME,
    version          = extract_version(),
    package_dir      = {'': 'lib'},
    packages         = extract_packages(),
    description      = "GRIB loading for Iris",
    long_description = LONG_DESCRIPTION,
    url              = 'https://github.com/SciTools/iris-grib',
    author           = 'UK Met Office',
    author_email     = 'scitools-iris@googlegroups.com',
    license          = 'LGPL',
    platforms        = "Linux, Mac OS X, Windows",
    keywords         = ['iris', 'GRIB'],
    classifiers      = [
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires = [
        'iris>=1.9,<2',
        # Also: the ECMWF GRIB API
    ],
    extras_require = {
        'test:python_version=="2.7"': ['mock'],
    },
    test_suite = '{}.tests'.format(NAME),
)


if __name__ == '__main__':
    setup(**setup_args)
