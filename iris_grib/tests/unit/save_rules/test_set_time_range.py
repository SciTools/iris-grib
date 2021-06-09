# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.set_time_range`

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock
import warnings

from cf_units import Unit
import gribapi

from iris.coords import DimCoord

from iris_grib._save_rules import set_time_range


class Test(tests.IrisGribTest):
    def setUp(self):
        self.coord = DimCoord(0, 'time',
                              units=Unit('hours since epoch',
                                         calendar='standard'))

    def test_no_bounds(self):
        with self.assertRaisesRegex(ValueError, 'Expected time coordinate '
                                    'with two bounds, got 0 bounds'):
            set_time_range(self.coord, mock.sentinel.grib)

    def test_three_bounds(self):
        self.coord.bounds = [0, 1, 2]
        with self.assertRaisesRegex(ValueError, 'Expected time coordinate '
                                    'with two bounds, got 3 bounds'):
            set_time_range(self.coord, mock.sentinel.grib)

    def test_non_scalar(self):
        coord = DimCoord([0, 1], 'time', bounds=[[0, 1], [1, 2]],
                         units=Unit('hours since epoch', calendar='standard'))
        with self.assertRaisesRegex(ValueError, 'Expected length one time '
                                    'coordinate, got 2 points'):
            set_time_range(coord, mock.sentinel.grib)

    @mock.patch.object(gribapi, 'grib_set')
    def test_hours(self, mock_set):
        lower = 10
        upper = 20
        self.coord.bounds = [lower, upper]
        set_time_range(self.coord, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeRange', 1)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'lengthOfTimeRange', upper - lower)

    @mock.patch.object(gribapi, 'grib_set')
    def test_days(self, mock_set):
        lower = 4
        upper = 6
        self.coord.bounds = [lower, upper]
        self.coord.units = Unit('days since epoch', calendar='standard')
        set_time_range(self.coord, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeRange', 1)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'lengthOfTimeRange',
                                 (upper - lower) * 24)

    @mock.patch.object(gribapi, 'grib_set')
    def test_fractional_hours(self, mock_set_long):
        lower = 10.0
        upper = 20.9
        self.coord.bounds = [lower, upper]
        with warnings.catch_warnings(record=True) as warn:
            warnings.simplefilter("always")
            set_time_range(self.coord, mock.sentinel.grib)
        self.assertEqual(len(warn), 1)
        msg = r'Truncating floating point lengthOfTimeRange 10\.8?9+ ' \
              'to integer value 10'
        self.assertRegex(str(warn[0].message), msg)
        mock_set_long.assert_any_call(mock.sentinel.grib,
                                      'indicatorOfUnitForTimeRange', 1)
        mock_set_long.assert_any_call(mock.sentinel.grib,
                                      'lengthOfTimeRange', int(upper - lower))


if __name__ == "__main__":
    tests.main()
