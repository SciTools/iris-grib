# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Unit tests for `iris_grib.grib_save_rules.reference_time`."""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

import gribapi

from iris_grib import load_cubes
from iris_grib._save_rules import reference_time


class Test(tests.IrisGribTest):
    def _test(self, cube):
        grib = mock.Mock()
        mock_gribapi = mock.Mock(spec=gribapi)
        with mock.patch('iris_grib._save_rules.gribapi', mock_gribapi):
            reference_time(cube, grib)

        mock_gribapi.assert_has_calls(
            [mock.call.grib_set_long(grib, "significanceOfReferenceTime", 1),
             mock.call.grib_set_long(grib, "dataDate", '19980306'),
             mock.call.grib_set_long(grib, "dataTime", '0300')])

    @tests.skip_data
    def test_forecast_period(self):
        # The stock cube has a non-compliant forecast_period.
        fname = tests.get_data_path(('GRIB', 'global_t', 'global.grib2'))
        [cube] = load_cubes(fname)
        self._test(cube)

    @tests.skip_data
    def test_no_forecast_period(self):
        # The stock cube has a non-compliant forecast_period.
        fname = tests.get_data_path(('GRIB', 'global_t', 'global.grib2'))
        [cube] = load_cubes(fname)
        cube.remove_coord("forecast_period")
        self._test(cube)


if __name__ == "__main__":
    tests.main()
