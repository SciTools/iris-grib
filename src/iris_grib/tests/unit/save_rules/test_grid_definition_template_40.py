# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Unit tests for :meth:`iris_grib._save_rules.is_grid_definition_template_40`
and :meth:`iris_grib._save_rules.grid_definition_template_40`.
"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests
import numpy as np
import iris.coords
from iris.coord_systems import GeogCS
from iris_grib._save_rules import (
    is_grid_definition_template_40,
    grid_definition_template_40,
)
from iris_grib.tests.unit.save_rules import GdtTestMixin


class TestIsGridDefinitionTemplate40(tests.IrisGribTest, GdtTestMixin):
    """Tests for is_grid_definition_template_40 validation function."""

    def setUp(self):
        self.default_ellipsoid = GeogCS(semi_major_axis=6371200.0)
        GdtTestMixin.setUp(self)

    def _make_gaussian_cube(self, x_points=None, y_points=None, grib_grid_template=40):
        """Create a cube suitable for GDT 40 (gaussian grid)."""
        if x_points is None or y_points is None:
            x_points = [0.0, 90.0, 180.0, 270.0] * 4
            y_points = [-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4
        cs = self.default_ellipsoid
        x_coord = iris.coords.AuxCoord(
            x_points, long_name="longitude", units="degrees", coord_system=cs
        )
        y_coord = iris.coords.AuxCoord(
            y_points, long_name="latitude", units="degrees", coord_system=cs
        )
        test_cube = iris.cube.Cube(np.zeros(len(y_points)))
        test_cube.add_aux_coord(y_coord, 0)
        test_cube.add_aux_coord(x_coord, 0)
        if grib_grid_template is not None:
            test_cube.attributes["GRIB2_GRID_TEMPLATE"] = grib_grid_template
        return test_cube

    def test__valid_gaussian_grid(self):
        """Test that a valid gaussian grid returns True."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertTrue(result)

    def test__missing_grib2_grid_template_attribute(self):
        """Test that missing GRIB2_GRID_TEMPLATE attribute returns False."""
        test_cube = self._make_gaussian_cube(grib_grid_template=None)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__wrong_grib2_grid_template_value(self):
        """Test that wrong GRIB2_GRID_TEMPLATE value returns False."""
        test_cube = self._make_gaussian_cube(grib_grid_template=4)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__grib2_grid_template_string_not_int(self):
        """Test that non-integer GRIB2_GRID_TEMPLATE value returns False."""
        test_cube = self._make_gaussian_cube()
        test_cube.attributes["GRIB2_GRID_TEMPLATE"] = "40"
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__different_coord_dimensions(self):
        """Test that coordinates with different dimensions return False."""
        test_cube = iris.cube.Cube(np.zeros((4, 3)))
        x_coord = iris.coords.DimCoord(
            [0.0, 120.0, 240.0],
            long_name="longitude",
            units="degrees",
            coord_system=self.default_ellipsoid,
        )
        y_coord = iris.coords.AuxCoord(
            [1.0, 2.0, 3.0, 4.0],
            long_name="latitude",
            units="degrees",
            coord_system=self.default_ellipsoid,
        )
        test_cube.add_dim_coord(x_coord, 1)
        test_cube.add_aux_coord(y_coord, 0)
        test_cube.attributes["GRIB2_GRID_TEMPLATE"] = 40
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__no_repeated_latitudes(self):
        """Test that coordinates with no repeated latitude values return False."""
        x_points = list(range(8))
        y_points = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__non_monotonic_latitudes(self):
        """Test that non-monotonic latitudes return False."""
        x_points = list(range(8))
        y_points = [-60.0, -60.0, -30.0, 0.0, -30.0, 30.0, 30.0, 60.0]
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__odd_number_unique_latitudes(self):
        """Test that odd number of unique latitude values returns False."""
        x_points = [0.0, 90.0, 0.0, 90.0, 0.0, 90.0]
        y_points = [-60.0, -60.0, 0.0, 0.0, 60.0, 60.0]
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__non_contiguous_latitudes(self):
        """Test that non-contiguous latitude blocks return False."""
        x_points = [0.0, 90.0, 180.0, 270.0, 0.0, 90.0, 180.0, 270.0]
        y_points = [-30.0, -30.0, 30.0, 30.0, -30.0, -30.0, 30.0, 30.0]
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__non_monotonic_longitudes_in_block(self):
        """Test that non-monotonic longitudes within a latitude block return False."""
        x_points = [0.0, 180.0, 90.0, 270.0, 0.0, 90.0, 180.0, 270.0]
        y_points = [-60.0, -60.0, -60.0, -60.0, 30.0, 30.0, 30.0, 30.0]
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertFalse(result)

    def test__valid_decreasing_latitudes(self):
        """Test that valid decreasing latitudes return True."""
        x_points = [0.0, 90.0, 180.0, 270.0] * 4
        y_points = [60.0] * 4 + [30.0] * 4 + [-30.0] * 4 + [-60.0] * 4
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertTrue(result)

    def test__valid_decreasing_longitudes(self):
        """Test that valid decreasing longitudes return True."""
        x_points = [270.0, 180.0, 90.0, 0.0] * 4
        y_points = [-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertTrue(result)

    def test__valid_varying_lon_counts_per_lat(self):
        """Test valid gaussian grid with varying lon counts per unique lat."""
        x_points = [0.0, 180.0, 0.0, 90.0, 180.0, 270.0]
        y_points = [-60.0, -60.0, 60.0, 60.0, 60.0, 60.0]
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = is_grid_definition_template_40(test_cube, x_coord, y_coord)
        self.assertTrue(result)


class TestGridDefinitionTemplate40(tests.IrisGribTest, GdtTestMixin):
    """Tests for grid_definition_template_40 function."""

    def setUp(self):
        self.default_ellipsoid = GeogCS(semi_major_axis=6371200.0)
        GdtTestMixin.setUp(self)

    def _make_gaussian_cube(self, x_points=None, y_points=None, grib_grid_template=40):
        """Create a cube suitable for GDT 40 (gaussian grid)."""
        if x_points is None or y_points is None:
            x_points = [0.0, 90.0, 180.0, 270.0] * 4
            y_points = [-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4
        cs = self.default_ellipsoid
        x_coord = iris.coords.AuxCoord(
            x_points, long_name="longitude", units="degrees", coord_system=cs
        )
        y_coord = iris.coords.AuxCoord(
            y_points, long_name="latitude", units="degrees", coord_system=cs
        )
        test_cube = iris.cube.Cube(np.zeros(len(y_points)))
        test_cube.add_aux_coord(y_coord, 0)
        test_cube.add_aux_coord(x_coord, 0)
        if grib_grid_template is not None:
            test_cube.attributes["GRIB2_GRID_TEMPLATE"] = grib_grid_template
        return test_cube

    def test__template_number(self):
        """Test that gridDefinitionTemplateNumber is set to 40."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("gridDefinitionTemplateNumber", 40)

    def test__latitude_of_first_grid_point(self):
        """Test that latitudeOfFirstGridPoint is set correctly."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("latitudeOfFirstGridPoint", int(-60.0e6))

    def test__latitude_of_last_grid_point(self):
        """Test that latitudeOfLastGridPoint is set correctly."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("latitudeOfLastGridPoint", int(60.0e6))

    def test__longitude_of_first_grid_point_increasing(self):
        """Test longitudeOfFirstGridPoint for increasing longitudes."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("longitudeOfFirstGridPoint", int(0.0e6))

    def test__longitude_of_last_grid_point_increasing(self):
        """Test longitudeOfLastGridPoint for increasing longitudes."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("longitudeOfLastGridPoint", int(270.0e6))

    def test__longitude_of_first_grid_point_decreasing(self):
        """Test longitudeOfFirstGridPoint for decreasing longitudes."""
        x_points = [270.0, 180.0, 90.0, 0.0] * 4
        y_points = [-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("longitudeOfFirstGridPoint", int(270.0e6))

    def test__longitude_of_last_grid_point_decreasing(self):
        """Test longitudeOfLastGridPoint for decreasing longitudes."""
        x_points = [270.0, 180.0, 90.0, 0.0] * 4
        y_points = [-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("longitudeOfLastGridPoint", int(0.0e6))

    def test__N_gaussian_coefficient(self):
        """Test that N (gaussian coefficient) is set correctly."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("N", 2)

    def test__Nj_total_latitudes(self):
        """Test that Nj (total number of latitude values) is set correctly."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("Nj", 4)

    def test__basic_angle_of_initial_production_domain(self):
        """Test that basicAngleOfTheInitialProductionDomain is set to 0."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("basicAngleOfTheInitialProductionDomain", 0)

    def test__resolution_and_component_flags(self):
        """Test that resolutionAndComponentFlags is set to 0."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("resolutionAndComponentFlags", 0)

    def test__number_of_octets_for_number_of_points(self):
        """Test that numberOfOctectsForNumberOfPoints is set to 2."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("numberOfOctectsForNumberOfPoints", 2)

    def test__interpretation_of_number_of_points(self):
        """Test that interpretationOfNumberOfPoints is set to 1."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("interpretationOfNumberOfPoints", 1)

    def test__pl_array_uniform_repeats(self):
        """Test that pl (points list) array is set correctly with uniform repeats."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("pl", [4, 4, 4, 4])

    def test__pl_array_varying_repeats(self):
        """Test that pl array is set correctly with varying lon counts."""
        x_points = [0.0, 180.0, 0.0, 90.0, 180.0, 270.0]
        y_points = [-60.0, -60.0, 60.0, 60.0, 60.0, 60.0]
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("pl", [2, 4])

    def test__return_value_is_grib(self):
        """Test that the function returns the grib object."""
        test_cube = self._make_gaussian_cube()
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        result = grid_definition_template_40(
            test_cube, self.mock_grib, x_coord, y_coord
        )
        self.assertIs(result, self.mock_grib)

    def test__coordinates_with_decreasing_latitudes(self):
        """Test with decreasing latitude values."""
        x_points = [0.0, 90.0, 180.0, 270.0] * 4
        y_points = [60.0] * 4 + [30.0] * 4 + [-30.0] * 4 + [-60.0] * 4
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("latitudeOfFirstGridPoint", int(60.0e6))
        self._check_key("latitudeOfLastGridPoint", int(-60.0e6))

    def test__coordinates_with_decreasing_longitudes(self):
        """Test with decreasing longitude values."""
        x_points = [270.0, 180.0, 90.0, 0.0] * 4
        y_points = [-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4
        test_cube = self._make_gaussian_cube(x_points=x_points, y_points=y_points)
        x_coord = test_cube.coord("longitude")
        y_coord = test_cube.coord("latitude")
        grid_definition_template_40(test_cube, self.mock_grib, x_coord, y_coord)
        self._check_key("longitudeOfFirstGridPoint", int(270.0e6))
        self._check_key("longitudeOfLastGridPoint", int(0.0e6))


if __name__ == "__main__":
    tests.main()
