# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Unit tests for `iris_grib.grib_save_rules.identification`."""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

import gribapi

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
