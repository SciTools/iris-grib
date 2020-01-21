# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.grid_definition_template_4`.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import numpy as np

from iris.coord_systems import GeogCS

from iris_grib._save_rules import grid_definition_template_4
from iris_grib.tests.unit.save_rules import GdtTestMixin


class Test(tests.IrisGribTest, GdtTestMixin):
    def setUp(self):
        GdtTestMixin.setUp(self)

    def test__template_number(self):
        grid_definition_template_4(self.test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 4)

    def test__shape_of_earth_spherical(self):
        cs = GeogCS(semi_major_axis=1.23)
        test_cube = self._make_test_cube(cs=cs)
        grid_definition_template_4(test_cube, self.mock_grib)
        self._check_key('shapeOfTheEarth', 1)
        self._check_key('scaleFactorOfRadiusOfSphericalEarth', 0)
        self._check_key('scaledValueOfRadiusOfSphericalEarth', 1.23)

    def test__shape_of_earth_flattened(self):
        cs = GeogCS(semi_major_axis=1.456,
                    semi_minor_axis=1.123)
        test_cube = self._make_test_cube(cs=cs)
        grid_definition_template_4(test_cube, self.mock_grib)
        self._check_key('shapeOfTheEarth', 7)
        self._check_key('scaleFactorOfEarthMajorAxis', 0)
        self._check_key('scaledValueOfEarthMajorAxis', 1.456)
        self._check_key('scaleFactorOfEarthMinorAxis', 0)
        self._check_key('scaledValueOfEarthMinorAxis', 1.123)

    def test__grid_shape(self):
        test_cube = self._make_test_cube(x_points=np.arange(13),
                                         y_points=np.arange(6))
        grid_definition_template_4(test_cube, self.mock_grib)
        self._check_key('Ni', 13)
        self._check_key('Nj', 6)

    def test__grid_points(self):
        x_floats = np.array([11.0, 12.0, 167.0])
        # TODO: reduce Y to 2 points, when gribapi nx=ny limitation is gone.
        y_floats = np.array([20.0, 21.0, 22.0])
        test_cube = self._make_test_cube(x_points=x_floats, y_points=y_floats)
        grid_definition_template_4(test_cube, self.mock_grib)
        x_longs = np.array(np.round(1e6 * x_floats), dtype=int)
        y_longs = np.array(np.round(1e6 * y_floats), dtype=int)
        self._check_key("longitudes", x_longs)
        self._check_key("latitudes", y_longs)

    def test__scanmode(self):
        grid_definition_template_4(self.test_cube, self.mock_grib)
        self._check_key('iScansPositively', 1)
        self._check_key('jScansPositively', 1)

    def test__scanmode_reverse(self):
        test_cube = self._make_test_cube(x_points=np.arange(7, 0, -1))
        grid_definition_template_4(test_cube, self.mock_grib)
        self._check_key('iScansPositively', 0)
        self._check_key('jScansPositively', 1)


if __name__ == "__main__":
    tests.main()
