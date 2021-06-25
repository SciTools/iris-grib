# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.product_definition_template_10`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris.coords import DimCoord
from iris_grib._load_convert import product_definition_template_10
from iris_grib.tests.unit.load_convert import empty_metadata


class Test(tests.IrisGribTest):
    def setUp(self):
        module = 'iris_grib._load_convert'
        self.patch_statistical_fp_coord = self.patch(
            module + '.statistical_forecast_period_coord',
            return_value=mock.sentinel.dummy_fp_coord)
        self.patch_time_coord = self.patch(
            module + '.validity_time_coord',
            return_value=mock.sentinel.dummy_time_coord)
        self.patch_vertical_coords = self.patch(module + '.vertical_coords')

    def test_percentile_coord(self):
        metadata = empty_metadata()
        percentileValue = 75
        section = {'productDefinitionTemplateNumber': 10,
                   'percentileValue': percentileValue,
                   'hoursAfterDataCutoff': 1,
                   'minutesAfterDataCutoff': 1,
                   'numberOfTimeRange': 1,
                   'typeOfStatisticalProcessing': 1,
                   'typeOfTimeIncrement': 2,
                   'timeIncrement': 0,
                   'yearOfEndOfOverallTimeInterval': 2000,
                   'monthOfEndOfOverallTimeInterval': 1,
                   'dayOfEndOfOverallTimeInterval': 1,
                   'hourOfEndOfOverallTimeInterval': 1,
                   'minuteOfEndOfOverallTimeInterval': 0,
                   'secondOfEndOfOverallTimeInterval': 1}
        forecast_reference_time = mock.Mock()
        # The called being tested.
        product_definition_template_10(section, metadata,
                                       forecast_reference_time)

        expected = {'aux_coords_and_dims': []}
        percentile = DimCoord(percentileValue,
                              long_name='percentile_over_time',
                              units='no_unit')
        expected['aux_coords_and_dims'].append((percentile, None))

        self.assertEqual(metadata['aux_coords_and_dims'][-1],
                         expected['aux_coords_and_dims'][0])


if __name__ == '__main__':
    tests.main()
