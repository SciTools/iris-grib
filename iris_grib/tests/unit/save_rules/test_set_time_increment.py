# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.set_time_increment`

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

import gribapi

from iris.coords import CellMethod

from iris_grib._save_rules import set_time_increment


class Test(tests.IrisGribTest):
    @mock.patch.object(gribapi, 'grib_set')
    def test_no_intervals(self, mock_set):
        cell_method = CellMethod('sum', 'time')
        set_time_increment(cell_method, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeIncrement', 255)
        mock_set.assert_any_call(mock.sentinel.grib, 'timeIncrement', 0)

    @mock.patch.object(gribapi, 'grib_set')
    def test_area(self, mock_set):
        cell_method = CellMethod('sum', 'area', '25 km')
        set_time_increment(cell_method, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeIncrement', 255)
        mock_set.assert_any_call(mock.sentinel.grib, 'timeIncrement', 0)

    @mock.patch.object(gribapi, 'grib_set')
    def test_multiple_intervals(self, mock_set):
        cell_method = CellMethod('sum', 'time', ('1 hour', '24 hour'))
        set_time_increment(cell_method, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeIncrement', 255)
        mock_set.assert_any_call(mock.sentinel.grib, 'timeIncrement', 0)

    @mock.patch.object(gribapi, 'grib_set')
    def test_hr(self, mock_set):
        cell_method = CellMethod('sum', 'time', '23 hr')
        set_time_increment(cell_method, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeIncrement', 1)
        mock_set.assert_any_call(mock.sentinel.grib, 'timeIncrement', 23)

    @mock.patch.object(gribapi, 'grib_set')
    def test_hour(self, mock_set):
        cell_method = CellMethod('sum', 'time', '24 hour')
        set_time_increment(cell_method, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeIncrement', 1)
        mock_set.assert_any_call(mock.sentinel.grib, 'timeIncrement', 24)

    @mock.patch.object(gribapi, 'grib_set')
    def test_hours(self, mock_set):
        cell_method = CellMethod('sum', 'time', '25 hours')
        set_time_increment(cell_method, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeIncrement', 1)
        mock_set.assert_any_call(mock.sentinel.grib, 'timeIncrement', 25)

    @mock.patch.object(gribapi, 'grib_set')
    def test_fractional_hours(self, mock_set):
        cell_method = CellMethod('sum', 'time', '25.9 hours')
        with mock.patch('warnings.warn') as warn:
            set_time_increment(cell_method, mock.sentinel.grib)
        warn.assert_called_once_with('Truncating floating point timeIncrement '
                                     '25.9 to integer value 25')
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'indicatorOfUnitForTimeIncrement', 1)
        mock_set.assert_any_call(mock.sentinel.grib, 'timeIncrement', 25)


if __name__ == "__main__":
    tests.main()
