# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for `iris_grib._load_convert.product_definition_template_31`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris_grib.tests.unit.load_convert import empty_metadata

from iris_grib._load_convert import product_definition_template_31


def section_4():
    # Also needed for test_product_definition_section.py.
    series = mock.sentinel.satelliteSeries
    number = mock.sentinel.satelliteNumber
    instrument = mock.sentinel.instrumentType
    return {'NB': 1,
            'satelliteSeries': series,
            'satelliteNumber': number,
            'instrumentType': instrument,
            'scaleFactorOfCentralWaveNumber': 1,
            'scaledValueOfCentralWaveNumber': 12}


class Test(tests.IrisGribTest):
    def setUp(self):
        self.patch('warnings.warn')
        self.satellite_common_patch = self.patch(
            'iris_grib._load_convert.satellite_common')
        self.generating_process_patch = self.patch(
            'iris_grib._load_convert.generating_process')

    def test(self):
        # Prepare the arguments.
        rt_coord = mock.sentinel.observation_time
        section = section_4()

        # Call the function.
        metadata = empty_metadata()
        product_definition_template_31(section, metadata, rt_coord)

        # Check that 'satellite_common' was called.
        self.assertEqual(self.satellite_common_patch.call_count, 1)
        # Check that 'generating_process' was called.
        self.assertEqual(self.generating_process_patch.call_count, 1)
        # Check that the scalar time coord was added in.
        self.assertIn((rt_coord, None), metadata['aux_coords_and_dims'])


if __name__ == '__main__':
    tests.main()
