# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Unit tests for :meth:`iris_grib._save_rules.grid_definition_template_40`.

"""

import numpy as np
import pytest

import eccodes

from iris.coords import AuxCoord, DimCoord
from iris.coord_systems import GeogCS
from iris.cube import Cube

import iris_grib._save_rules as save_rules
from iris_grib._save_rules import (
    grid_definition_template_40,
    is_grid_definition_template_40,
)


def make_gaussian_cube(
    x_points=None,
    y_points=None,
    grib_grid_template=40,
    semi_major_axis=6371200.0,
    semi_minor_axis=None,
    patch_eccodes_getarrays=None,
):
    if x_points is None or y_points is None:
        # commonest cases have increasing lons + decreasing lats, so mimic that
        x_points = [0.0, 90.0, 180.0, 270.0] * 4
        y_points = [60.0] * 4 + [30.0] * 4 + [-30.0] * 4 + [-60.0] * 4
    if semi_minor_axis is None:
        ellipsoid = GeogCS(semi_major_axis=semi_major_axis)
    else:
        ellipsoid = GeogCS(
            semi_major_axis=semi_major_axis,
            semi_minor_axis=semi_minor_axis,
        )
    x_coord = AuxCoord(
        x_points, long_name="longitude", units="degrees", coord_system=ellipsoid
    )
    y_coord = AuxCoord(
        y_points, long_name="latitude", units="degrees", coord_system=ellipsoid
    )
    cube = Cube(np.zeros(len(y_points)))
    cube.add_aux_coord(y_coord, 0)
    cube.add_aux_coord(x_coord, 0)
    if grib_grid_template is not None:
        cube.attributes["GRIB2_GRID_TEMPLATE"] = grib_grid_template

    if patch_eccodes_getarrays is not None:

        def array_results(grib, key, ktype=None):
            return {"longitudes": x_coord.points, "latitudes": y_coord.points}[key]

        patch_eccodes_getarrays.codes_get_array = array_results

    return cube, x_coord, y_coord


@pytest.fixture
def mock_grib(mocker):
    return mocker.Mock(keys={})


@pytest.fixture
def patched_eccodes(mocker):
    class _FakeECCodes:
        @staticmethod
        def codes_set(grib, name, value):
            grib.keys[name] = value

        codes_set_long = codes_set
        codes_set_float = codes_set
        codes_set_double = codes_set
        codes_set_long_array = codes_set
        codes_set_array = codes_set

        @staticmethod
        def codes_set_missing(grib, name):
            grib.keys[name] = "MISSING"

    fake = _FakeECCodes()
    mocker.patch.object(save_rules, "eccodes", fake)
    return fake


class TestIsGridDefinitionTemplate40:
    def test_true_for_valid_grid(self):
        cube, _, _ = make_gaussian_cube()
        assert is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_missing_attribute(self):
        cube, _, _ = make_gaussian_cube(grib_grid_template=None)
        assert not is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_wrong_attribute_value(self):
        cube, _, _ = make_gaussian_cube(grib_grid_template=4)
        assert not is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_attribute_not_int(self):
        cube, _, _ = make_gaussian_cube()
        cube.attributes["GRIB2_GRID_TEMPLATE"] = "40"
        assert not is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_different_coord_dimensions(self):
        ellipsoid = GeogCS(semi_major_axis=6371200.0)
        cube = Cube(np.zeros((4, 3)))
        x_coord = DimCoord(
            [0.0, 120.0, 240.0],
            long_name="longitude",
            units="degrees",
            coord_system=ellipsoid,
        )
        y_coord = AuxCoord(
            [1.0, 2.0, 3.0, 4.0],
            long_name="latitude",
            units="degrees",
            coord_system=ellipsoid,
        )
        cube.add_dim_coord(x_coord, 1)
        cube.add_aux_coord(y_coord, 0)
        cube.attributes["GRIB2_GRID_TEMPLATE"] = 40
        assert not is_grid_definition_template_40(cube, x_coord, y_coord)

    def test_true_with_decreasing_latitudes(self):
        cube, _, _ = make_gaussian_cube(
            x_points=[0.0, 90.0, 180.0, 270.0] * 4,
            y_points=[60.0] * 4 + [30.0] * 4 + [-30.0] * 4 + [-60.0] * 4,
        )
        assert is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_true_with_decreasing_longitudes(self):
        cube, _, _ = make_gaussian_cube(
            x_points=[270.0, 180.0, 90.0, 0.0] * 4,
            y_points=[-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4,
        )
        assert is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_true_with_varying_lon_counts_per_lat(self):
        cube, _, _ = make_gaussian_cube(
            x_points=[0.0, 180.0, 0.0, 90.0, 180.0, 270.0],
            y_points=[-60.0, -60.0, 60.0, 60.0, 60.0, 60.0],
        )
        assert is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )


class TestGridDefinitionTemplate40:
    def test_writes_expected_core_keys(self, mock_grib, patched_eccodes):
        cube, x_coord, y_coord = make_gaussian_cube(
            patch_eccodes_getarrays=patched_eccodes
        )
        grid_definition_template_40(cube, mock_grib, x_coord, y_coord)

        assert mock_grib.keys["gridType"] == "reduced_gg"
        # From shape_of_the_earth() using the default spherical GeogCS.
        assert mock_grib.keys["shapeOfTheEarth"] == 1
        assert mock_grib.keys["scaledValueOfRadiusOfSphericalEarth"] == 6371200.0
        # From scanning_mode_flags(): default has +x and non-+y (first 2 lats equal).
        assert mock_grib.keys["scanningMode"] == 0
        assert mock_grib.keys["latitudeOfFirstGridPoint"] == int(60.0e6)
        assert mock_grib.keys["latitudeOfLastGridPoint"] == int(-60.0e6)
        assert mock_grib.keys["longitudeOfFirstGridPoint"] == int(0.0e6)
        assert mock_grib.keys["longitudeOfLastGridPoint"] == int(270.0e6)
        assert mock_grib.keys["N"] == 2
        assert mock_grib.keys["Nj"] == 4
        assert mock_grib.keys["basicAngleOfTheInitialProductionDomain"] == 0
        assert mock_grib.keys["resolutionAndComponentFlags"] == 0
        assert mock_grib.keys["Ni"] == "MISSING"
        assert mock_grib.keys["iDirectionIncrement"] == "MISSING"
        assert mock_grib.keys["numberOfOctectsForNumberOfPoints"] == 2
        assert mock_grib.keys["interpretationOfNumberOfPoints"] == 1
        assert mock_grib.keys["pl"] == [4, 4, 4, 4]

    def test_writes_shape_of_earth_fixed_6(self, mock_grib, patched_eccodes):
        cube, x_coord, y_coord = make_gaussian_cube(
            semi_major_axis=6371229.0,
            patch_eccodes_getarrays=patched_eccodes,
        )
        grid_definition_template_40(cube, mock_grib, x_coord, y_coord)
        assert mock_grib.keys["shapeOfTheEarth"] == 6
        assert mock_grib.keys["scaleFactorOfEarthMajorAxis"] == 0
        assert mock_grib.keys["scaledValueOfEarthMajorAxis"] == 0
        assert mock_grib.keys["scaleFactorOfEarthMinorAxis"] == 0
        assert mock_grib.keys["scaledValueOfEarthMinorAxis"] == 0

    def test_writes_decreasing_lons(self, mock_grib, patched_eccodes):
        "Test the less-usual X scan direction."
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=[270.0, 180.0, 90.0, 0.0] * 4,
            y_points=[60.0] * 4 + [30.0] * 4 + [-30.0] * 4 + [-60.0] * 4,
            patch_eccodes_getarrays=patched_eccodes,
        )
        grid_definition_template_40(cube, mock_grib, x_coord, y_coord)
        assert mock_grib.keys["longitudeOfFirstGridPoint"] == int(270.0e6)
        assert mock_grib.keys["longitudeOfLastGridPoint"] == int(0.0e6)
        # Opposite X scan direction sets bit 1 (0x80).
        assert mock_grib.keys["scanningMode"] == 0x80

    def test_writes_increasing_lats(self, mock_grib, patched_eccodes):
        "Test the less-usual Y scan direction."
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=[0.0, 90.0, 180.0, 270.0] * 4,
            y_points=[-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4,
            patch_eccodes_getarrays=patched_eccodes,
        )
        grid_definition_template_40(cube, mock_grib, x_coord, y_coord)
        assert mock_grib.keys["latitudeOfFirstGridPoint"] == int(-60.0e6)
        assert mock_grib.keys["latitudeOfLastGridPoint"] == int(60.0e6)
        # Positive Y scan direction sets bit 2 (0x40).
        assert mock_grib.keys["scanningMode"] == 0x40

    def test_writes_pl_with_varying_lon_counts(self, mock_grib, patched_eccodes):
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=[0.0, 180.0, 0.0, 90.0, 180.0, 270.0],
            y_points=[-60.0, -60.0, 60.0, 60.0, 60.0, 60.0],
            patch_eccodes_getarrays=patched_eccodes,
        )
        grid_definition_template_40(cube, mock_grib, x_coord, y_coord)
        assert mock_grib.keys["N"] == 1
        assert mock_grib.keys["Nj"] == 2
        assert mock_grib.keys["pl"] == [2, 4]

    def test_fails_no_repeated_latitudes(self, mock_grib, patched_eccodes):
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=list(range(8)),
            y_points=[0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0],
            patch_eccodes_getarrays=patched_eccodes,
        )
        msg = "Latitudes have no repeated values."
        with pytest.raises(ValueError, match=msg):
            grid_definition_template_40(cube, mock_grib, x_coord, y_coord)

    def test_fails_non_monotonic_latitudes(self, mock_grib, patched_eccodes):
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
            y_points=[-60.0, -60.0, -30.0, 0.0, -30.0, 30.0, 30.0, 60.0],
        )
        msg = "Latitudes are not monotonic."
        with pytest.raises(ValueError, match=msg):
            grid_definition_template_40(cube, mock_grib, x_coord, y_coord)

    def test_fails_odd_number_unique_latitudes(self, mock_grib, patched_eccodes):
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=[0.0, 90.0, 0.0, 90.0, 0.0, 90.0],
            y_points=[-60.0, -60.0, 0.0, 0.0, 60.0, 60.0],
            patch_eccodes_getarrays=patched_eccodes,
        )
        msg = r"Number of distinct latitude repeat sections, 'N \* 2', is not even."
        with pytest.raises(ValueError, match=msg):
            grid_definition_template_40(cube, mock_grib, x_coord, y_coord)

    def test_fails_non_contiguous_latitudes(self, mock_grib, patched_eccodes):
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=[0.0, 90.0, 180.0, 45.0, 0.0, 90.0, 180.0, 0.0, 90.0, 180.0],
            y_points=[0.0, 0.0, 0.0, 20.0, 30.0, 30.0, 30.0, 70.0, 70.0, 70.0],
            patch_eccodes_getarrays=patched_eccodes,
        )
        msg = "Latitude value of 20.0 occurs only 1 times, must be >= 2."
        with pytest.raises(ValueError, match=msg):
            grid_definition_template_40(cube, mock_grib, x_coord, y_coord)

    def test_fails_non_monotonic_longitudes_within_lat_block(
        self, mock_grib, patched_eccodes
    ):
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=[0.0, 180.0, 90.0, 270.0, 0.0, 90.0, 180.0, 270.0],
            y_points=[-60.0, -60.0, -60.0, -60.0, 30.0, 30.0, 30.0, 30.0],
            patch_eccodes_getarrays=patched_eccodes,
        )
        msg = "Longitude values for latitude -60.0 are not monotonic."
        with pytest.raises(ValueError, match=msg):
            grid_definition_template_40(cube, mock_grib, x_coord, y_coord)

    def test_fails_different_lon_directions_between_latitudes(
        self, mock_grib, patched_eccodes
    ):
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=[0.0, 90.0, 180.0, 270.0, 270.0, 180.0, 90.0, 0.0],
            y_points=[-60.0] * 4 + [60.0] * 4,
        )
        msg = "Longitude values do not go in the same direction for all latitudes."
        with pytest.raises(ValueError, match=msg):
            grid_definition_template_40(cube, mock_grib, x_coord, y_coord)

    def test_fails_when_eccodes_latitudes_do_not_match(self):
        """Test via a *real* grib message, with incorrect latitude values."""
        x_points = [0.0, 90.0, 180.0, 270.0] * 4
        # latitudes that look structurally ~OK, but are not correct gaussian latitudes
        y_points = [80.0] * 4 + [20.0] * 4 + [-20.0] * 4 + [-80.0] * 4
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=x_points, y_points=y_points
        )
        grib = eccodes.codes_grib_new_from_samples("GRIB2")
        msg = (
            "Cube y coordinate values do not match the expected latitude values "
            "for a reduced gaussian grid with the given dimensions."
        )
        with pytest.raises(ValueError, match=msg):
            grid_definition_template_40(cube, grib, x_coord, y_coord)

    def test_fails_when_eccodes_longitudes_do_not_match(self):
        """Test via a *real* grib message, with correct lats but bad lons."""
        # latitudes that are the correct gaussian latitudes for N=2
        y_points = [59.4444] * 4 + [19.8757] * 4 + [-19.8757] * 4 + [-59.4444] * 4
        # longitudes that look ~OK, but with one point 'off' a bit
        x_points = [0.0, 90.0, 180.0, 270.0] * 4
        x_points[6] += 25.0
        cube, x_coord, y_coord = make_gaussian_cube(
            x_points=x_points, y_points=y_points
        )
        grib = eccodes.codes_grib_new_from_samples("GRIB2")
        msg = (
            "Cube x coordinate values do not match the expected longitude values "
            "for a reduced gaussian grid with the given dimensions."
        )
        with pytest.raises(ValueError, match=msg):
            grid_definition_template_40(cube, grib, x_coord, y_coord)
