# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.product_definition_template_15`

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

from cf_units import Unit
import gribapi

from iris.coords import CellMethod, DimCoord
import iris.tests.stock as stock

from iris_grib._save_rules import product_definition_template_15


class TestSpatialProcessingIdentifiers(tests.IrisGribTest):
    def setUp(self):
        self.cube = stock.lat_lon_cube()
        # Add scalar time coord so that product_definition_template_common
        # doesn't get upset.
        t_coord = DimCoord([424854.], standard_name='time',
                           units=Unit('hours since 1970-01-01 00:00:00',
                                      calendar='gregorian'))
        self.cube.add_aux_coord(t_coord)
        # Rename cube to avoid warning about unknown discipline/parameter.
        self.cube.rename('air_temperature')

    @mock.patch.object(gribapi, 'grib_set')
    def test_cell_method(self, mock_set):
        cube_0 = self.cube
        cube_0.attributes = dict(spatial_processing_type='No interpolation')
        cell_method = CellMethod(method='mean', coords=['area'])
        cube_0.add_cell_method(cell_method)

        # If the cube has a cell method attached then it should not have any
        # interpolation on the data, so spatial processing code should be 0 and
        # number of points used should be 0.
        product_definition_template_15(cube_0, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 15)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "spatialProcessing", 0)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "statisticalProcess", 0)

    @mock.patch.object(gribapi, 'grib_set')
    def test_bilinear_interpolation(self, mock_set):
        cube_1 = self.cube
        cube_1.attributes = dict(spatial_processing_type='Bilinear '
                                                         'interpolation')

        # If the cube has a bilinear interpolation attribute, spatial
        # processing code should be 1 and number of points used should be 4.
        product_definition_template_15(cube_1, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 15)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "spatialProcessing", 1)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "numberOfPointsUsed", 4)

    @mock.patch.object(gribapi, 'grib_set')
    def test_bicubic_interpolation(self, mock_set):
        cube_2 = self.cube
        cube_2.attributes = dict(spatial_processing_type='Bicubic '
                                                         'interpolation')

        # If the cube has a bicubic interpolation attribute, spatial
        # processing code should be 2 and number of points used should be 4.
        product_definition_template_15(cube_2, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 15)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "spatialProcessing", 2)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "numberOfPointsUsed", 4)

    @mock.patch.object(gribapi, 'grib_set')
    def test_nearest_neighbour_interpolation(self, mock_set):
        cube_3 = self.cube
        cube_3.attributes = dict(spatial_processing_type='Nearest neighbour '
                                                         'interpolation')

        # If the cube has a nearest neighbour interpolation attribute, spatial
        # processing code should be 3 and number of points used should be 1.
        product_definition_template_15(cube_3, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 15)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "spatialProcessing", 3)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "numberOfPointsUsed", 1)

    @mock.patch.object(gribapi, 'grib_set')
    def test_budget_interpolation(self, mock_set):
        cube_4 = self.cube
        cube_4.attributes = dict(spatial_processing_type='Budget '
                                                         'interpolation')

        # If the cube has a budget interpolation attribute, spatial
        # processing code should be 4 and number of points used should be 4.
        product_definition_template_15(cube_4, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 15)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "spatialProcessing", 4)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "numberOfPointsUsed", 4)

    @mock.patch.object(gribapi, 'grib_set')
    def test_spectral_interpolation(self, mock_set):
        cube_5 = self.cube
        cube_5.attributes = dict(spatial_processing_type='Spectral '
                                                         'interpolation')

        # If the cube has a spectral interpolation attribute, spatial
        # processing code should be 5 and number of points used should be 4.
        product_definition_template_15(cube_5, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 15)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "spatialProcessing", 5)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "numberOfPointsUsed", 4)

    @mock.patch.object(gribapi, 'grib_set')
    def test_neighbour_budget_interpolation(self, mock_set):
        cube_6 = self.cube
        cube_6.attributes = dict(spatial_processing_type='Neighbour-budget '
                                                         'interpolation')

        # If the cube has a neighbour-budget interpolation attribute, spatial
        # processing code should be 6 and number of points used should be 4.
        product_definition_template_15(cube_6, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 15)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "spatialProcessing", 6)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "numberOfPointsUsed", 4)


if __name__ == "__main__":
    tests.main()
