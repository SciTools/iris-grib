# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for function
:func:`iris_grib._load_convert.product_definition_template_8`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris_grib._load_convert import product_definition_template_8


class Test(tests.IrisGribTest):
    def setUp(self):
        module = 'iris_grib._load_convert'
        self.module = module
        # Create patches for called routines
        self.patch_generating_process = self.patch(
            module + '.generating_process')
        self.patch_data_cutoff = self.patch(module + '.data_cutoff')
        self.patch_statistical_cell_method = self.patch(
            module + '.statistical_cell_method',
            return_value=mock.sentinel.dummy_cell_method)
        self.patch_statistical_fp_coord = self.patch(
            module + '.statistical_forecast_period_coord',
            return_value=mock.sentinel.dummy_fp_coord)
        self.patch_time_coord = self.patch(
            module + '.validity_time_coord',
            return_value=mock.sentinel.dummy_time_coord)
        self.patch_vertical_coords = self.patch(module + '.vertical_coords')
        # Construct dummy call arguments
        self.section = {}
        self.section['hoursAfterDataCutoff'] = mock.sentinel.cutoff_hours
        self.section['minutesAfterDataCutoff'] = mock.sentinel.cutoff_mins
        self.frt_coord = mock.Mock()
        self.metadata = {'cell_methods': [], 'aux_coords_and_dims': []}

    def test_basic(self):
        product_definition_template_8(
            self.section, self.metadata, self.frt_coord)
        # Check all expected functions were called just once.
        self.assertEqual(self.patch_generating_process.call_count, 1)
        self.assertEqual(self.patch_data_cutoff.call_count, 1)
        self.assertEqual(self.patch_statistical_cell_method.call_count, 1)
        self.assertEqual(self.patch_statistical_fp_coord.call_count, 1)
        self.assertEqual(self.patch_time_coord.call_count, 1)
        self.assertEqual(self.patch_vertical_coords.call_count, 1)
        # Check metadata content.
        self.assertEqual(sorted(self.metadata.keys()),
                         ['aux_coords_and_dims', 'cell_methods'])
        self.assertEqual(self.metadata['cell_methods'],
                         [mock.sentinel.dummy_cell_method])
        self.assertCountEqual(self.metadata['aux_coords_and_dims'],
                              [(self.frt_coord, None),
                               (mock.sentinel.dummy_fp_coord, None),
                               (mock.sentinel.dummy_time_coord, None)])


if __name__ == '__main__':
    tests.main()
