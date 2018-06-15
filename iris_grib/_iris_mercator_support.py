# (C) British Crown Copyright 2018, Met Office
#
# This file is part of iris-grib.
#
# iris-grib is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-grib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-grib.  If not, see <http://www.gnu.org/licenses/>.
"""
Temporary module to check for the extended Mercator class in Iris,
which iris-grib requires for its Mercator support.

"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa
import six

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
