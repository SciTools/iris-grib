# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for `iris_grib._load_convert.product_definition_template_32`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris_grib.tests.unit.load_convert import empty_metadata
from iris_grib._load_convert import product_definition_template_32


class Test(tests.IrisGribTest):
    def setUp(self):
        self.patch('warnings.warn')
        self.generating_process_patch = self.patch(
            'iris_grib._load_convert.generating_process')
        self.satellite_common_patch = self.patch(
            'iris_grib._load_convert.satellite_common')
        self.time_coords_patch = self.patch(
            'iris_grib._load_convert.time_coords')
        self.data_cutoff_patch = self.patch(
            'iris_grib._load_convert.data_cutoff')

    def test(self, value=10, factor=1):
        # Prepare the arguments.
        series = mock.sentinel.satelliteSeries
        number = mock.sentinel.satelliteNumber
        instrument = mock.sentinel.instrumentType
        rt_coord = mock.sentinel.observation_time
        section = {'NB': 1,
                   'hoursAfterDataCutoff': None,
                   'minutesAfterDataCutoff': None,
                   'satelliteSeries': series,
                   'satelliteNumber': number,
                   'instrumentType': instrument,
                   'scaleFactorOfCentralWaveNumber': 1,
                   'scaledValueOfCentralWaveNumber': 12,
                   }

        # Call the function.
        metadata = empty_metadata()
        product_definition_template_32(section, metadata, rt_coord)

        # Check that 'satellite_common' was called.
        self.assertEqual(self.satellite_common_patch.call_count, 1)
        # Check that 'generating_process' was called.
        self.assertEqual(self.generating_process_patch.call_count, 1)
        # Check that 'data_cutoff' was called.
        self.assertEqual(self.data_cutoff_patch.call_count, 1)
        # Check that 'time_coords' was called.
        self.assertEqual(self.time_coords_patch.call_count, 1)


if __name__ == '__main__':
    tests.main()
