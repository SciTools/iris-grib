# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Temporary module to check for the extended Mercator class in Iris,
which iris-grib requires for its Mercator support.

"""

import distutils.version

import iris


def confirm_extended_mercator_supported():
    # Check that Iris version is at least 2.1, required for 'standard_parallel'
    # support in the Mercator coord-system.
    # This is a temporary fix allowing us to state Iris>=2.0 as a dependency,
    # required for this release because Iris 2.1 is not yet available.
    iris_version = distutils.version.LooseVersion(iris.__version__)
    min_mercator_version = '2.1.0'
    if iris_version < min_mercator_version:
        msg = 'Support for Mercator projections requires Iris version >= {}'
        raise ValueError(msg.format(min_mercator_version))
