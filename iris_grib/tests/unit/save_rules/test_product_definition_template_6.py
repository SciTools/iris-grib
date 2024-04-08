# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.product_definition_template_6`

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

from cf_units import Unit
import eccodes

from iris.coords import DimCoord
import iris.tests.stock as stock

from iris_grib._save_rules import product_definition_template_6


class TestRealizationIdentifier(tests.IrisGribTest):
    def setUp(self):
        self.cube = stock.lat_lon_cube()
        # Rename cube to avoid warning about unknown discipline/parameter.
        self.cube.rename('air_temperature')
        coord = DimCoord([45], 'time',
                         units=Unit('days since epoch', calendar='standard'))
        self.cube.add_aux_coord(coord)

    @mock.patch.object(eccodes, 'codes_set')
    def test_percentile(self, mock_set):
        cube = self.cube
        coord = DimCoord(10, long_name='percentile', units='%')
        cube.add_aux_coord(coord)

        product_definition_template_6(cube, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 6)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "percentileValue", 10)

    @mock.patch.object(eccodes, 'codes_set')
    def test_multiple_percentile_values(self, mock_set):
        cube = self.cube
        coord = DimCoord([8, 9, 10], long_name='percentile', units='%')
        cube.add_aux_coord(coord, 0)

        msg = "'percentile' coordinate with one point is required"
        with self.assertRaisesRegex(ValueError, msg):
            product_definition_template_6(cube, mock.sentinel.grib)


if __name__ == "__main__":
    tests.main()
