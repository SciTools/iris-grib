# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for function
:func:`iris_grib._load_convert.statistical_cell_method`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.coords import CellMethod
from iris.exceptions import TranslationError

from iris_grib._load_convert import statistical_cell_method


class Test(tests.IrisGribTest):
    def setUp(self):
        self.section = {}
        self.section['productDefinitionTemplateNumber'] = 8
        self.section['numberOfTimeRange'] = 1
        self.section['typeOfStatisticalProcessing'] = 0
        self.section['typeOfTimeIncrement'] = 2
        self.section['timeIncrement'] = 0

    def expected_cell_method(self,
                             coords=('time',), method='mean', intervals=None):
        keys = dict(coords=coords, method=method, intervals=intervals)
        cell_method = CellMethod(**keys)
        return cell_method

    def test_basic(self):
        cell_method = statistical_cell_method(self.section)
        self.assertEqual(cell_method, self.expected_cell_method())

    def test_intervals(self):
        self.section['timeIncrement'] = 3
        self.section['indicatorOfUnitForTimeIncrement'] = 1
        cell_method = statistical_cell_method(self.section)
        self.assertEqual(cell_method,
                         self.expected_cell_method(intervals=('3 hours',)))

    def test_increment_missing(self):
        self.section['timeIncrement'] = 2 ** 32 - 1
        self.section['indicatorOfUnitForTimeIncrement'] = 255
        cell_method = statistical_cell_method(self.section)
        self.assertEqual(cell_method, self.expected_cell_method())

    def test_different_statistic(self):
        self.section['typeOfStatisticalProcessing'] = 6
        cell_method = statistical_cell_method(self.section)
        self.assertEqual(
            cell_method,
            self.expected_cell_method(method='standard_deviation'))

    def test_fail_bad_ranges(self):
        self.section['numberOfTimeRange'] = 0
        with self.assertRaisesRegex(TranslationError,
                                    'aggregation over "0 time ranges"'):
            statistical_cell_method(self.section)

    def test_fail_multiple_ranges(self):
        self.section['numberOfTimeRange'] = 2
        with self.assertRaisesRegex(TranslationError,
                                    r'multiple time ranges \[2\]'):
            statistical_cell_method(self.section)

    def test_fail_unknown_statistic(self):
        self.section['typeOfStatisticalProcessing'] = 17
        with self.assertRaisesRegex(
                TranslationError,
                r'contains an unsupported statistical process type \[17\]'):
            statistical_cell_method(self.section)

    def test_fail_bad_increment_type(self):
        self.section['typeOfTimeIncrement'] = 7
        with self.assertRaisesRegex(
                TranslationError,
                r'time-increment type \[7\] is not supported'):
            statistical_cell_method(self.section)

    def test_pdt_9(self):
        # Should behave the same as PDT 4.8.
        self.section['productDefinitionTemplateNumber'] = 9
        cell_method = statistical_cell_method(self.section)
        self.assertEqual(cell_method, self.expected_cell_method())

    def test_pdt_10(self):
        # Should behave the same as PDT 4.8.
        self.section['productDefinitionTemplateNumber'] = 10
        cell_method = statistical_cell_method(self.section)
        self.assertEqual(cell_method, self.expected_cell_method())

    def test_pdt_11(self):
        # Should behave the same as PDT 4.8.
        self.section['productDefinitionTemplateNumber'] = 11
        cell_method = statistical_cell_method(self.section)
        self.assertEqual(cell_method, self.expected_cell_method())

    def test_pdt_15(self):
        # Encoded slightly differently to PDT 4.8.
        self.section['productDefinitionTemplateNumber'] = 15
        test_code = self.section['typeOfStatisticalProcessing']
        del self.section['typeOfStatisticalProcessing']
        self.section['statisticalProcess'] = test_code
        cell_method = statistical_cell_method(self.section)
        self.assertEqual(cell_method, self.expected_cell_method())

    def test_fail_unsupported_pdt(self):
        # Rejects PDTs other than the ones tested above.
        self.section['productDefinitionTemplateNumber'] = 101
        msg = "can't get statistical method for unsupported pdt : 4.101"
        with self.assertRaisesRegex(ValueError, msg):
            statistical_cell_method(self.section)


if __name__ == '__main__':
    tests.main()
