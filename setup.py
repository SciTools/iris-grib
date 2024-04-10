#!/usr/bin/env python

import os
import os.path
from setuptools import setup

NAME = 'iris_grib'
PYPI_NAME = 'iris-grib'
PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
PACKAGE_ROOT = os.path.join(PACKAGE_DIR, NAME)

packages = []
for d, _, _ in os.walk(os.path.join(PACKAGE_DIR, NAME)):
    if os.path.exists(os.path.join(d, '__init__.py')):
        packages.append(d[len(PACKAGE_DIR) + 1:].replace(os.path.sep, '.'))


def pip_requirements(*args):
    requirements = []
    for name in args:
        fname = os.path.join(
            PACKAGE_DIR, "requirements", "{}.txt".format(name)
        )
        if not os.path.exists(fname):
            emsg = (
                f"Unable to find the {name!r} requirements file at {fname!r}"
            )
            raise RuntimeError(emsg)
        with open(fname, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                requirements.append(line)
    return requirements


def extract_version():
    version = None
    fname = os.path.join(PACKAGE_DIR, 'iris_grib', '__init__.py')
    with open(fname) as fi:
        for line in fi:
            if (line.startswith('__version__')):
                _, version = line.split('=')
                version = version.strip()[1:-1]  # Remove quotations
                break
    return version


def long_description():
    fname = os.path.join(PACKAGE_DIR, "README.rst")
    with open(fname, "rb") as fi:
        result = fi.read().decode("utf-8")
    return result


def file_walk_relative(top, remove=''):
    """
    Returns a generator of files from the top of the tree, removing
    the given prefix from the root/file result.

    """
    top = top.replace('/', os.path.sep)
    remove = remove.replace('/', os.path.sep)
    for root, dirs, files in os.walk(top):
        for file in files:
            yield os.path.join(root, file).replace(remove, '')


setup_args = dict(
    name             = PYPI_NAME,                                # noqa: E221,E251,E501
    version          = extract_version(),                        # noqa: E221,E251,E501
    packages         = packages,                                 # noqa: E221,E251,E501
    package_data     = {'iris_grib': list(                       # noqa: E221,E251,E501
        file_walk_relative('iris_grib/tests/results', remove='iris_grib/'))
    },
    description      = "GRIB loading for Iris",                  # noqa: E221,E251,E501
    long_description = long_description(),                       # noqa: E221,E251,E501
    long_description_content_type = "text/x-rst",                # noqa: E221,E251,E501
    url              = 'https://github.com/SciTools/iris-grib',  # noqa: E221,E251,E501
    author           = 'UK Met Office',                          # noqa: E221,E251,E501
    author_email     = 'scitools-iris@googlegroups.com',         # noqa: E221,E251,E501
    license          = 'BSD',                                    # noqa: E221,E251,E501
    platforms        = "Linux, Mac OS X, Windows",               # noqa: E221,E251,E501
    keywords         = ['iris', 'GRIB'],                         # noqa: E221,E251,E501
    classifiers=[                                                # noqa: E221,E251,E501
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3 :: Only',
    ],
    # NOTE: The Python 3 bindings to eccodes (eccodes-python) is available on
    # PyPI, but the user is required to install eccodes itself manually. See
    # ECMWF ecCodes installation documentation for more information.
    install_requires=pip_requirements("setup", "core"),
    test_loader="unittest:TestLoader",
    extras_require={
        "all": pip_requirements("all"),
        "test": pip_requirements("test"),
    },
)


if __name__ == '__main__':
    setup(**setup_args)
