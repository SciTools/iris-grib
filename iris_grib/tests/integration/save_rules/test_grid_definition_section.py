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
Integration tests for :func:`iris_grib._save_rules.grid_definition_section`
to confirm that the correct grid_definition_template is being selected.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris.coords import DimCoord
from iris.coord_systems import (GeogCS,
                                RotatedGeogCS,
                                TransverseMercator,
                                LambertConformal,
                                AlbersEqualArea)
from iris.cube import Cube
import numpy as np

from iris_grib._save_rules import grid_definition_section
from iris_grib.tests.unit.save_rules import GdtTestMixin


class Test(tests.IrisGribTest, GdtTestMixin):
    def setUp(self):
        GdtTestMixin.setUp(self)
        self.ellipsoid = GeogCS(6371200)

    def _make_cube(self, x_points, y_points, cs, coord_units='1'):
        x_coord = DimCoord(x_points, long_name='x', units=coord_units,
                           coord_system=cs)
        y_coord = DimCoord(y_points, long_name='y', units=coord_units,
                           coord_system=cs)
        dcad = [(y_coord, 0), (x_coord, 1)]
        return Cube(np.zeros((len(x_points), len(y_points))),
                    dim_coords_and_dims=dcad)

    def test_grid_definition_template_0(self):
        # Regular lat/lon (Plate Carree).
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'degrees'
        cs = self.ellipsoid
        test_cube = self._make_cube(x_points, y_points, cs, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 0)

    def test_grid_definition_template_1(self):
        # Rotated lat/lon (Plate Carree).
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'degrees'
        cs = RotatedGeogCS(34.0, 117.0, ellipsoid=self.ellipsoid)
        test_cube = self._make_cube(x_points, y_points, cs, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 1)

    def test_grid_definition_template_4(self):
        # Irregular (variable resolution) lat/lon grid.
        x_points = np.array([0, 2, 7])
        y_points = np.array([1, 3, 6])
        cs = self.ellipsoid
        test_cube = self._make_cube(x_points, y_points, cs)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 4)

    def test_grid_definition_template_5(self):
        # Irregular (variable resolution) rotated lat/lon grid.
        x_points = np.array([0, 2, 7])
        y_points = np.array([1, 3, 6])
        cs = RotatedGeogCS(34.0, 117.0, ellipsoid=self.ellipsoid)
        test_cube = self._make_cube(x_points, y_points, cs)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 5)

    def test_grid_definition_template_12(self):
        # Transverse Mercator grid.
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'm'
        cs = TransverseMercator(0, 0, 0, 0, 1, ellipsoid=self.ellipsoid)
        test_cube = self._make_cube(x_points, y_points, cs, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 12)

    def test_grid_definition_template_30(self):
        # Lambert Conformal grid.
        x_points = np.arange(3)
        y_points = np.arange(3)
        coord_units = 'm'
        cs = LambertConformal(ellipsoid=self.ellipsoid)
        test_cube = self._make_cube(x_points, y_points, cs, coord_units)
        grid_definition_section(test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 30)

    def test_coord_system_not_supported(self):
        # Test an unsupported grid - let's choose Albers Equal Area.
        x_points = np.arange(3)
        y_points = np.arange(3)
        cs = AlbersEqualArea(ellipsoid=self.ellipsoid)
        test_cube = self._make_cube(x_points, y_points, cs)

        exp_name = cs.grid_mapping_name.replace('_', ' ').title()
        exp_emsg = 'not supported for coordinate system {!r}'.format(exp_name)
        with self.assertRaisesRegexp(ValueError, exp_emsg):
            grid_definition_section(test_cube, self.mock_grib)


if __name__ == "__main__":
    tests.main()
