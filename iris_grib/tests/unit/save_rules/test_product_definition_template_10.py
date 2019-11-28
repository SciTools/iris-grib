# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.product_definition_template_10`

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

from cf_units import Unit
import gribapi

from iris.coords import DimCoord
import iris.tests.stock as stock

from iris_grib._save_rules import product_definition_template_10


class TestPercentileValueIdentifier(tests.IrisGribTest):
    def setUp(self):
        self.cube = stock.lat_lon_cube()
        # Rename cube to avoid warning about unknown discipline/parameter.
        self.cube.rename('y_wind')
        time_coord = DimCoord(
            20, 'time', bounds=[0, 40],
            units=Unit('days since epoch', calendar='julian'))
        self.cube.add_aux_coord(time_coord)

    @mock.patch.object(gribapi, 'grib_set')
    def test_percentile_value(self, mock_set):
        cube = self.cube
        percentile_coord = DimCoord(95, long_name='percentile_over_time')
        cube.add_aux_coord(percentile_coord)

        product_definition_template_10(cube, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 10)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "percentileValue", 95)

    @mock.patch.object(gribapi, 'grib_set')
    def test_multiple_percentile_value(self, mock_set):
        cube = self.cube
        percentile_coord = DimCoord([5, 10, 15],
                                    long_name='percentile_over_time')
        cube.add_aux_coord(percentile_coord, 0)
        err_msg = "A cube 'percentile_over_time' coordinate with one point "\
                  "is required"
        with self.assertRaisesRegex(ValueError, err_msg):
            product_definition_template_10(cube, mock.sentinel.grib)


if __name__ == "__main__":
    tests.main()
