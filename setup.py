#!/usr/bin/env python
from __future__ import print_function

import os
import os.path
from setuptools import setup
import textwrap


name = 'iris_grib'


LONG_DESCRIPTION = textwrap.dedent("""
    Iris loading of GRIB files
    ==========================

    With this package, iris is able to load GRIB files:

    ```
    my_data = iris.load(path_to_grib_file)
    ```
    """)


here = os.path.abspath(os.path.dirname(__file__))
pkg_root = os.path.join(here, name)

packages = []
for d, _, _ in os.walk(os.path.join(here, name)):
    if os.path.exists(os.path.join(d, '__init__.py')):
        packages.append(d[len(here)+1:].replace(os.path.sep, '.'))

package_data = {
    'iris_grib': ['iris_grib/tests/results/*'],
}


def extract_version():
    version = None
    fdir = os.path.dirname(__file__)
    fnme = os.path.join(fdir, 'iris_grib', '__init__.py')
    with open(fnme) as fd:
        for line in fd:
            if (line.startswith('__version__')):
                _, version = line.split('=')
                version = version.strip()[1:-1]  # Remove quotation characters
                break
    return version


setup_args = dict(
    name             = name,
    version          = extract_version(),
    packages         = packages,
    package_data     = package_data,
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
        'test': ['nose'],
    },
)


if __name__ == '__main__':
    setup(**setup_args)
