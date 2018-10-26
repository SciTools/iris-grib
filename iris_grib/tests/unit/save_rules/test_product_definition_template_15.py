# (C) British Crown Copyright 2018, Met Office
#
# This file is part of iris-grib.
#
# iris-grib is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-grib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-grib.  If not, see <http://www.gnu.org/licenses/>.
"""
Unit tests for :func:`iris_grib._save_rules.product_definition_template_15`

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from cf_units import Unit
import gribapi
import mock

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
        self.cube.rename('WAFC_CAT_potential')

    @mock.patch.object(gribapi, 'grib_set')
    def test_cell_method(self, mock_set):
        cube_0 = self.cube
        cube_0.attributes = dict(spatial_processing_type=0)
        cell_method = CellMethod(method='mean', coords=['area'])
        cube_0.add_cell_method(cell_method)

        # If the cube has a cell method attached then it should not have any
        # interpolation on the data, so spatial processing code should be 0 and
        # number of points used should be 1.
        product_definition_template_15(cube_0, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 15)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "spatialProcessing", 0)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "numberOfPointsUsed", 1)

    @mock.patch.object(gribapi, 'grib_set')
    def test_bilinear_interpolation(self, mock_set):
        cube_1 = self.cube
        cube_1.attributes = dict(spatial_processing_type=1)

        # Currently no implemented recognition of spatial processing code 1,
        # so check that an error is raised if we try and save it.
        msg = ('Cannot save Product Definition Type 4.15 with spatial '
               'processing type {}'.format(1))
        with self.assertRaisesRegexp(ValueError, msg):
            product_definition_template_15(cube_1, mock.sentinel.grib)

    @mock.patch.object(gribapi, 'grib_set')
    def test_bicubic_interpolation(self, mock_set):
        cube_2 = self.cube
        cube_2.attributes = dict(spatial_processing_type=2)

        # Currently no implemented recognition of spatial processing code 2,
        # so check that an error is raised if we try and save it.
        msg = ('Cannot save Product Definition Type 4.15 with spatial '
               'processing type {}'.format(2))
        with self.assertRaisesRegexp(ValueError, msg):
            product_definition_template_15(cube_2, mock.sentinel.grib)

    @mock.patch.object(gribapi, 'grib_set')
    def test_nearest_neighbour_interpolation(self, mock_set):
        cube_3 = self.cube
        cube_3.attributes = dict(spatial_processing_type=3)

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
        cube_4.attributes = dict(spatial_processing_type=4)

        # Currently no implemented recognition of spatial processing code 4,
        # so check that an error is raised if we try and save it.
        msg = ('Cannot save Product Definition Type 4.15 with spatial '
               'processing type {}'.format(4))
        with self.assertRaisesRegexp(ValueError, msg):
            product_definition_template_15(cube_4, mock.sentinel.grib)

    @mock.patch.object(gribapi, 'grib_set')
    def test_spectral_interpolation(self, mock_set):
        cube_5 = self.cube
        cube_5.attributes = dict(spatial_processing_type=5)

        # Currently no implemented recognition of spatial processing code 5,
        # so check that an error is raised if we try and save it.
        msg = ('Cannot save Product Definition Type 4.15 with spatial '
               'processing type {}'.format(5))
        with self.assertRaisesRegexp(ValueError, msg):
            product_definition_template_15(cube_5, mock.sentinel.grib)

    @mock.patch.object(gribapi, 'grib_set')
    def test_neighbour_budget__interpolation(self, mock_set):
        cube_6 = self.cube
        cube_6.attributes = dict(spatial_processing_type=6)

        # Currently no implemented recognition of spatial processing code 6,
        # so check that an error is raised if we try and save it.
        msg = ('Cannot save Product Definition Type 4.15 with spatial '
               'processing type {}'.format(6))
        with self.assertRaisesRegexp(ValueError, msg):
            product_definition_template_15(cube_6, mock.sentinel.grib)

if __name__ == "__main__":
    tests.main()
