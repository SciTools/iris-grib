# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for function :func:`iris_grib._load_convert.statistical_forecast_period`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import datetime
from unittest import mock

from iris_grib._load_convert import statistical_forecast_period_coord


class Test(tests.IrisGribTest):
    def setUp(self):
        module = 'iris_grib._load_convert'
        self.module = module
        self.patch_hindcast = self.patch(module + '._hindcast_fix')
        self.forecast_seconds = 0.0
        self.forecast_units = mock.Mock()
        self.forecast_units.convert = lambda x, y: self.forecast_seconds
        self.patch(module + '.time_range_unit',
                   return_value=self.forecast_units)
        self.frt_coord = mock.Mock()
        self.frt_coord.points = [1]
        self.frt_coord.units.num2date = mock.Mock(
            return_value=datetime.datetime(2010, 2, 3))
        self.section = {}
        self.section['yearOfEndOfOverallTimeInterval'] = 2010
        self.section['monthOfEndOfOverallTimeInterval'] = 2
        self.section['dayOfEndOfOverallTimeInterval'] = 3
        self.section['hourOfEndOfOverallTimeInterval'] = 8
        self.section['minuteOfEndOfOverallTimeInterval'] = 0
        self.section['secondOfEndOfOverallTimeInterval'] = 0
        self.section['forecastTime'] = mock.Mock()
        self.section['indicatorOfUnitOfTimeRange'] = mock.Mock()

    def test_basic(self):
        coord = statistical_forecast_period_coord(self.section,
                                                  self.frt_coord)
        self.assertEqual(coord.standard_name, 'forecast_period')
        self.assertEqual(coord.units, 'hours')
        self.assertArrayAlmostEqual(coord.points, [4.0])
        self.assertArrayAlmostEqual(coord.bounds, [[0.0, 8.0]])

    def test_with_hindcast(self):
        _ = statistical_forecast_period_coord(self.section, self.frt_coord)
        self.assertEqual(self.patch_hindcast.call_count, 1)

    def test_no_hindcast(self):
        self.patch(self.module + '.options.support_hindcast_values', False)
        _ = statistical_forecast_period_coord(self.section, self.frt_coord)
        self.assertEqual(self.patch_hindcast.call_count, 0)


if __name__ == '__main__':
    tests.main()
