# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration tests for :func:`iris_grib._save_rules.grid_definition_section`
to confirm that the correct grid_definition_template is being selected.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris.coord_systems import (GeogCS,
                                RotatedGeogCS,
                                Mercator,
                                TransverseMercator,
                                LambertConformal,
                                AlbersEqualArea)
import numpy as np

from iris_grib._save_rules import grid_definition_section
from iris_grib.tests.unit.save_rules import GdtTestMixin


class Test(tests.IrisGribTest, GdtTestMixin):
    def setUp(self):
        GdtTestMixin.setUp(self)
        self.ellipsoid = GeogCS(6371200)

    def test_grid_definition_template_0(self):
        # Regular lat/lon (Plate Carree).
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'degrees'
        cs = self.ellipsoid
        test_cube = self._make_test_cube(cs, x_points, y_points, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 0)

    def test_grid_definition_template_1(self):
        # Rotated lat/lon (Plate Carree).
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'degrees'
        cs = RotatedGeogCS(34.0, 117.0, ellipsoid=self.ellipsoid)
        test_cube = self._make_test_cube(cs, x_points, y_points, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 1)

    def test_grid_definition_template_4(self):
        # Irregular (variable resolution) lat/lon grid.
        x_points = np.array([0, 2, 7])
        y_points = np.array([1, 3, 6])
        coord_units = '1'
        cs = self.ellipsoid
        test_cube = self._make_test_cube(cs, x_points, y_points, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 4)

    def test_grid_definition_template_5(self):
        # Irregular (variable resolution) rotated lat/lon grid.
        x_points = np.array([0, 2, 7])
        y_points = np.array([1, 3, 6])
        coord_units = '1'
        cs = RotatedGeogCS(34.0, 117.0, ellipsoid=self.ellipsoid)
        test_cube = self._make_test_cube(cs, x_points, y_points, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 5)

    def test_grid_definition_template_10(self):
        # Mercator grid.
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'm'
        cs = Mercator(ellipsoid=self.ellipsoid)
        test_cube = self._make_test_cube(cs, x_points, y_points, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 10)

    def test_grid_definition_template_12(self):
        # Transverse Mercator grid.
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'm'
        cs = TransverseMercator(0, 0, 0, 0, 1, ellipsoid=self.ellipsoid)
        test_cube = self._make_test_cube(cs, x_points, y_points, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 12)

    def test_grid_definition_template_30(self):
        # Lambert Conformal grid.
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'm'
        cs = LambertConformal(ellipsoid=self.ellipsoid)
        test_cube = self._make_test_cube(cs, x_points, y_points, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 30)

    def test_coord_system_not_supported(self):
        # Test an unsupported grid - let's choose Albers Equal Area.
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = '1'
        cs = AlbersEqualArea(ellipsoid=self.ellipsoid)
        test_cube = self._make_test_cube(cs, x_points, y_points, coord_units)

        exp_name = cs.grid_mapping_name.replace('_', ' ').title()
        exp_emsg = 'not supported for coordinate system {!r}'.format(exp_name)
        with self.assertRaisesRegex(ValueError, exp_emsg):
            grid_definition_section(test_cube, self.mock_grib)


if __name__ == "__main__":
    tests.main()
