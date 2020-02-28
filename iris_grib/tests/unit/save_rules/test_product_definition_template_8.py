# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.product_definition_template_8`

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

from cf_units import Unit
import gribapi
import numpy as np

from iris.coords import CellMethod, DimCoord
import iris.cube
import iris.tests.stock as stock

from iris_grib._save_rules import product_definition_template_8


class TestProductDefinitionIdentifier(tests.IrisGribTest):
    def setUp(self):
        self.cube = stock.lat_lon_cube()
        # Rename cube to avoid warning about unknown discipline/parameter.
        self.cube.rename('air_temperature')
        coord = DimCoord(23, 'time', bounds=[0, 100],
                         units=Unit('days since epoch', calendar='standard'))
        self.cube.add_aux_coord(coord)

    @mock.patch.object(gribapi, 'grib_set')
    def test_product_definition(self, mock_set):
        cube = self.cube
        cell_method = CellMethod(method='sum', coords=['time'])
        cube.add_cell_method(cell_method)

        product_definition_template_8(cube, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 "productDefinitionTemplateNumber", 8)


class Test_type_of_statistical_processing(tests.IrisTest):
    @mock.patch.object(gribapi, "grib_set")
    def test_stats_type_min(self, mock_set):
        grib = None
        cube = iris.cube.Cube(np.array([1.0]))
        time_unit = Unit("hours since 1970-01-01 00:00:00")
        time_coord = iris.coords.DimCoord(
            [0.0], bounds=[0.0, 1], standard_name="time", units=time_unit
        )
        cube.add_aux_coord(time_coord, ())
        cube.add_cell_method(iris.coords.CellMethod("maximum", time_coord))
        product_definition_template_8(cube, grib)
        mock_set.assert_any_call(grib, "typeOfStatisticalProcessing", 2)

    @mock.patch.object(gribapi, "grib_set")
    def test_stats_type_max(self, mock_set):
        grib = None
        cube = iris.cube.Cube(np.array([1.0]))
        time_unit = Unit("hours since 1970-01-01 00:00:00")
        time_coord = iris.coords.DimCoord(
            [0.0], bounds=[0.0, 1], standard_name="time", units=time_unit
        )
        cube.add_aux_coord(time_coord, ())
        cube.add_cell_method(iris.coords.CellMethod("minimum", time_coord))
        product_definition_template_8(cube, grib)
        mock_set.assert_any_call(grib, "typeOfStatisticalProcessing", 3)


if __name__ == "__main__":
    tests.main()
