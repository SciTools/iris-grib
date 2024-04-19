# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Unit tests for :meth:`iris_grib._save_rules.grid_definition_template_20`.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris.coord_systems import GeogCS, PolarStereographic, Stereographic
from iris.coords import AuxCoord
from iris.exceptions import TranslationError
import numpy as np

from iris_grib._save_rules import grid_definition_template_20
from iris_grib.tests.unit.save_rules import GdtTestMixin


class Test(tests.IrisGribTest, GdtTestMixin):
    def setUp(self):
        self.default_ellipsoid = GeogCS(semi_major_axis=6371200.0)
        self.stereo_test_cube = self._make_test_cube(coord_units="m")

        GdtTestMixin.setUp(self)

    def _default_coord_system(self, false_easting=0, false_northing=0):
        return PolarStereographic(
            90.0,
            0,
            false_easting=false_easting,
            false_northing=false_northing,
            ellipsoid=self.default_ellipsoid,
        )

    def test__template_number(self):
        grid_definition_template_20(self.stereo_test_cube, self.mock_grib)
        self._check_key("gridDefinitionTemplateNumber", 20)

    def test__shape_of_earth(self):
        grid_definition_template_20(self.stereo_test_cube, self.mock_grib)
        self._check_key("shapeOfTheEarth", 1)
        self._check_key("scaleFactorOfRadiusOfSphericalEarth", 0)
        self._check_key("scaleFactorOfEarthMajorAxis", 0)
        self._check_key("scaledValueOfEarthMajorAxis", 0)
        self._check_key("scaleFactorOfEarthMinorAxis", 0)
        self._check_key("scaledValueOfEarthMinorAxis", 0)

    def test__grid_shape(self):
        stereo_test_cube = self._make_test_cube(
            x_points=np.arange(13), y_points=np.arange(6), coord_units="m"
        )
        grid_definition_template_20(stereo_test_cube, self.mock_grib)
        self._check_key("Nx", 13)
        self._check_key("Ny", 6)

    def test__grid_points(self):
        stereo_test_cube = self._make_test_cube(
            x_points=[1e6, 3e6, 5e6, 7e6], y_points=[4e6, 9e6], coord_units="m"
        )
        grid_definition_template_20(stereo_test_cube, self.mock_grib)
        self._check_key("latitudeOfFirstGridPoint", 54139565)
        self._check_key("longitudeOfFirstGridPoint", 165963757)
        self._check_key("Dx", 2e9)
        self._check_key("Dy", 5e9)

    def test__template_specifics(self):
        grid_definition_template_20(self.stereo_test_cube, self.mock_grib)
        self._check_key("LaD", 90e6)
        self._check_key("LoV", 0)

    def test__scanmode(self):
        grid_definition_template_20(self.stereo_test_cube, self.mock_grib)
        self._check_key("iScansPositively", 1)
        self._check_key("jScansPositively", 1)

    def test__scanmode_reverse(self):
        stereo_test_cube = self._make_test_cube(
            x_points=np.arange(7e6, 0, -1e6), coord_units="m"
        )
        grid_definition_template_20(stereo_test_cube, self.mock_grib)
        self._check_key("iScansPositively", 0)
        self._check_key("jScansPositively", 1)

    def test_projection_centre(self):
        grid_definition_template_20(self.stereo_test_cube, self.mock_grib)
        self._check_key("projectionCentreFlag", 0)

    def test_projection_centre_south_pole(self):
        cs = PolarStereographic(-90.0, 0, ellipsoid=self.default_ellipsoid)
        stereo_test_cube = self._make_test_cube(cs=cs, coord_units="m")
        grid_definition_template_20(stereo_test_cube, self.mock_grib)
        self._check_key("projectionCentreFlag", 128)

    def test_projection_centre_south_pole_parent(self):
        # Saving should be able to handle either class (PolarStereographic
        #  being a subclass of Stereographic).
        cs = Stereographic(-90.0, 0, ellipsoid=self.default_ellipsoid)
        stereo_test_cube = self._make_test_cube(cs=cs, coord_units="m")
        grid_definition_template_20(stereo_test_cube, self.mock_grib)
        self._check_key("projectionCentreFlag", 128)

    def test_projection_centre_bad(self):
        cs = Stereographic(0, 0, ellipsoid=self.default_ellipsoid)
        stereo_test_cube = self._make_test_cube(cs=cs, coord_units="m")
        exp_emsg = "Bipolar and symmetric .* not supported."
        with self.assertRaisesRegex(TranslationError, exp_emsg):
            grid_definition_template_20(stereo_test_cube, self.mock_grib)

    def __fail_false_easting_northing(self, false_easting, false_northing):
        cs = self._default_coord_system(
            false_easting=false_easting, false_northing=false_northing
        )
        test_cube = self._make_test_cube(cs=cs)
        message = "Non-zero unsupported"
        with self.assertRaisesRegex(TranslationError, message):
            grid_definition_template_20(test_cube, self.mock_grib)

    def test__fail_false_easting(self):
        self.__fail_false_easting_northing(10.0, 0.0)

    def test__fail_false_northing(self):
        self.__fail_false_easting_northing(0.0, 10.0)

    def test__fail_false_easting_northing(self):
        self.__fail_false_easting_northing(10.0, 10.0)

    def __fail_irregular_coords(self, x=False, y=False):
        def irregular_coord(coord):
            coord = AuxCoord.from_coord(coord)
            coord.points[1] = coord.points[0]
            return coord

        test_cube = self._make_test_cube(
            # Make the Y dimension longer to make irregularity is possible.
            y_points=[7.0, 8.0, 9.0],
            coord_units="m",
        )
        coord_lon = test_cube.coord("longitude")
        coord_lat = test_cube.coord("latitude")
        if x:
            test_cube.replace_coord(irregular_coord(coord_lon))
        if y:
            test_cube.replace_coord(irregular_coord(coord_lat))

        message = "Irregular coordinates not supported"
        with self.assertRaisesRegex(TranslationError, message):
            grid_definition_template_20(test_cube, self.mock_grib)

    def test__fail_irregular_x_coords(self):
        self.__fail_irregular_coords(x=True)

    def test__fail_irregular_y_coords(self):
        self.__fail_irregular_coords(y=True)

    def test__fail_irregular_coords(self):
        self.__fail_irregular_coords(x=True, y=True)

    def test__fail_non_identical_lats(self):
        coord_system = PolarStereographic(
            90.0,
            0,
            true_scale_lat=60.0,
            ellipsoid=self.default_ellipsoid,
        )
        test_cube = self._make_test_cube(cs=coord_system, coord_units="m")
        message = "only write a GRIB Template 3.20 file where these are identical"
        with self.assertRaisesRegex(TranslationError, message):
            grid_definition_template_20(test_cube, self.mock_grib)

    def test__fail_scale_factor(self):
        coord_system = PolarStereographic(
            90.0,
            0,
            scale_factor_at_projection_origin=0.5,
            ellipsoid=self.default_ellipsoid,
        )
        test_cube = self._make_test_cube(cs=coord_system, coord_units="m")
        message = "cannot write scale_factor_at_projection_origin"
        with self.assertRaisesRegex(TranslationError, message):
            grid_definition_template_20(test_cube, self.mock_grib)


if __name__ == "__main__":
    tests.main()
