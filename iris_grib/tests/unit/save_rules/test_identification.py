# (C) British Crown Copyright 2016, Met Office
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
"""Unit tests for `iris_grib.grib_save_rules.identification`."""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import gribapi
import mock

import iris
import iris.tests.stock as stock

from iris_grib._save_rules import identification
from iris_grib.tests.unit import TestGribSimple


GRIB_API = 'iris_grib._save_rules.gribapi'


class Test(TestGribSimple):
    @tests.skip_data
    def test_no_realization(self):
        cube = stock.simple_pp()
        grib = mock.Mock()
        mock_gribapi = mock.Mock(spec=gribapi)
        with mock.patch(GRIB_API, mock_gribapi):
            identification(cube, grib)

        mock_gribapi.assert_has_calls(
            [mock.call.grib_set_long(grib, "typeOfProcessedData", 2)])

    @tests.skip_data
    def test_realization_0(self):
        cube = stock.simple_pp()
        realisation = iris.coords.AuxCoord((0,), standard_name='realization',
                                           units='1')
        cube.add_aux_coord(realisation)

        grib = mock.Mock()
        mock_gribapi = mock.Mock(spec=gribapi)
        with mock.patch(GRIB_API, mock_gribapi):
            identification(cube, grib)

        mock_gribapi.assert_has_calls(
            [mock.call.grib_set_long(grib, "typeOfProcessedData", 3)])

    @tests.skip_data
    def test_realization_n(self):
        cube = stock.simple_pp()
        realisation = iris.coords.AuxCoord((2,), standard_name='realization',
                                           units='1')
        cube.add_aux_coord(realisation)

        grib = mock.Mock()
        mock_gribapi = mock.Mock(spec=gribapi)
        with mock.patch(GRIB_API, mock_gribapi):
            identification(cube, grib)

        mock_gribapi.assert_has_calls(
            [mock.call.grib_set_long(grib, "typeOfProcessedData", 4)])


if __name__ == "__main__":
    tests.main()
