# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :meth:`iris_grib._save_rules.grid_definition_template_30`.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import numpy as np

import iris.coords
from iris.coord_systems import GeogCS, LambertConformal

from iris_grib._save_rules import grid_definition_template_30
from iris_grib.tests.unit.save_rules import GdtTestMixin


class FakeGribError(Exception):
    pass


class Test(tests.IrisGribTest, GdtTestMixin):
    def setUp(self):
        self.default_ellipsoid = GeogCS(semi_major_axis=6377563.396,
                                        semi_minor_axis=6356256.909)
        self.test_cube = self._make_test_cube()

        GdtTestMixin.setUp(self)

    def _make_test_cube(self, cs=None, x_points=None, y_points=None):
        # Create a cube with given properties, or minimal defaults.
        if cs is None:
            cs = self._default_coord_system()
        if x_points is None:
            x_points = self._default_x_points()
        if y_points is None:
            y_points = self._default_y_points()

        x_coord = iris.coords.DimCoord(x_points, 'projection_x_coordinate',
                                       units='m', coord_system=cs)
        y_coord = iris.coords.DimCoord(y_points, 'projection_y_coordinate',
                                       units='m', coord_system=cs)
        test_cube = iris.cube.Cube(np.zeros((len(y_points), len(x_points))))
        test_cube.add_dim_coord(y_coord, 0)
        test_cube.add_dim_coord(x_coord, 1)
        return test_cube

    def _default_coord_system(self):
        return LambertConformal(central_lat=39.0, central_lon=-96.0,
                                false_easting=0.0, false_northing=0.0,
                                secant_latitudes=(33, 45),
                                ellipsoid=self.default_ellipsoid)

    def test__template_number(self):
        grid_definition_template_30(self.test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 30)

    def test__shape_of_earth(self):
        grid_definition_template_30(self.test_cube, self.mock_grib)
        self._check_key('shapeOfTheEarth', 7)
        self._check_key('scaleFactorOfEarthMajorAxis', 0)
        self._check_key('scaledValueOfEarthMajorAxis', 6377563.396)
        self._check_key('scaleFactorOfEarthMinorAxis', 0)
        self._check_key('scaledValueOfEarthMinorAxis', 6356256.909)

    def test__grid_shape(self):
        test_cube = self._make_test_cube(x_points=np.arange(13),
                                         y_points=np.arange(6))
        grid_definition_template_30(test_cube, self.mock_grib)
        self._check_key('Nx', 13)
        self._check_key('Ny', 6)

    def test__grid_points(self):
        test_cube = self._make_test_cube(x_points=[1e6, 3e6, 5e6, 7e6],
                                         y_points=[4e6, 9e6])
        grid_definition_template_30(test_cube, self.mock_grib)
        self._check_key("latitudeOfFirstGridPoint", 71676530)
        self._check_key("longitudeOfFirstGridPoint", 287218188)
        self._check_key("Dx", 2e9)
        self._check_key("Dy", 5e9)

    def test__template_specifics(self):
        grid_definition_template_30(self.test_cube, self.mock_grib)
        self._check_key("LaD", 39e6)
        self._check_key("LoV", 264e6)
        self._check_key("Latin1", 33e6)
        self._check_key("Latin2", 45e6)
        self._check_key("latitudeOfSouthernPole", 0)
        self._check_key("longitudeOfSouthernPole", 0)

    def test__scanmode(self):
        grid_definition_template_30(self.test_cube, self.mock_grib)
        self._check_key('iScansPositively', 1)
        self._check_key('jScansPositively', 1)

    def test__scanmode_reverse(self):
        test_cube = self._make_test_cube(x_points=np.arange(7e6, 0, -1e6))
        grid_definition_template_30(test_cube, self.mock_grib)
        self._check_key('iScansPositively', 0)
        self._check_key('jScansPositively', 1)

    def test_projection_centre(self):
        grid_definition_template_30(self.test_cube, self.mock_grib)
        self._check_key("projectionCentreFlag", 0)

    def test_projection_centre_south_pole(self):
        cs = LambertConformal(central_lat=39.0, central_lon=-96.0,
                              false_easting=0.0, false_northing=0.0,
                              secant_latitudes=(-33, -45),
                              ellipsoid=self.default_ellipsoid)
        test_cube = self._make_test_cube(cs=cs)
        grid_definition_template_30(test_cube, self.mock_grib)
        self._check_key("projectionCentreFlag", 1)


if __name__ == "__main__":
    tests.main()
