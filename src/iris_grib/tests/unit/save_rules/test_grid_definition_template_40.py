# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""Unit tests for GDT 3.40 save rules."""

import iris_grib.tests as tests  # noqa: F401  # required side-effect import

import numpy as np
import pytest

from iris.coords import AuxCoord, DimCoord
from iris.coord_systems import GeogCS
from iris.cube import Cube

import iris_grib._save_rules as save_rules


def make_gaussian_cube(x_points=None, y_points=None, grib_grid_template=40):
    if x_points is None or y_points is None:
        x_points = [0.0, 90.0, 180.0, 270.0] * 4
        y_points = [-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4
    ellipsoid = GeogCS(semi_major_axis=6371200.0)
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
    return cube


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
        cube = make_gaussian_cube()
        assert save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_missing_attribute(self):
        cube = make_gaussian_cube(grib_grid_template=None)
        assert not save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_wrong_attribute_value(self):
        cube = make_gaussian_cube(grib_grid_template=4)
        assert not save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_attribute_not_int(self):
        cube = make_gaussian_cube()
        cube.attributes["GRIB2_GRID_TEMPLATE"] = "40"
        assert not save_rules.is_grid_definition_template_40(
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
        assert not save_rules.is_grid_definition_template_40(cube, x_coord, y_coord)

    def test_false_no_repeated_latitudes(self):
        cube = make_gaussian_cube(
            x_points=list(range(8)),
            y_points=[0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0],
        )
        assert not save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_non_monotonic_latitudes(self):
        cube = make_gaussian_cube(
            x_points=list(range(8)),
            y_points=[-60.0, -60.0, -30.0, 0.0, -30.0, 30.0, 30.0, 60.0],
        )
        assert not save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_odd_number_unique_latitudes(self):
        cube = make_gaussian_cube(
            x_points=[0.0, 90.0, 0.0, 90.0, 0.0, 90.0],
            y_points=[-60.0, -60.0, 0.0, 0.0, 60.0, 60.0],
        )
        assert not save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_non_contiguous_latitudes(self):
        cube = make_gaussian_cube(
            x_points=[0.0, 90.0, 180.0, 270.0, 0.0, 90.0, 180.0, 270.0],
            y_points=[-30.0, -30.0, 30.0, 30.0, -30.0, -30.0, 30.0, 30.0],
        )
        assert not save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_false_non_monotonic_longitudes_within_lat_block(self):
        cube = make_gaussian_cube(
            x_points=[0.0, 180.0, 90.0, 270.0, 0.0, 90.0, 180.0, 270.0],
            y_points=[-60.0, -60.0, -60.0, -60.0, 30.0, 30.0, 30.0, 30.0],
        )
        assert not save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_true_with_decreasing_latitudes(self):
        cube = make_gaussian_cube(
            x_points=[0.0, 90.0, 180.0, 270.0] * 4,
            y_points=[60.0] * 4 + [30.0] * 4 + [-30.0] * 4 + [-60.0] * 4,
        )
        assert save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_true_with_decreasing_longitudes(self):
        cube = make_gaussian_cube(
            x_points=[270.0, 180.0, 90.0, 0.0] * 4,
            y_points=[-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4,
        )
        assert save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )

    def test_true_with_varying_lon_counts_per_lat(self):
        cube = make_gaussian_cube(
            x_points=[0.0, 180.0, 0.0, 90.0, 180.0, 270.0],
            y_points=[-60.0, -60.0, 60.0, 60.0, 60.0, 60.0],
        )
        assert save_rules.is_grid_definition_template_40(
            cube, cube.coord("longitude"), cube.coord("latitude")
        )


class TestGridDefinitionTemplate40:
    def test_writes_expected_core_keys(self, mock_grib, patched_eccodes):
        cube = make_gaussian_cube()
        x_coord = cube.coord("longitude")
        y_coord = cube.coord("latitude")
        returned = save_rules.grid_definition_template_40(
            cube, mock_grib, x_coord, y_coord
        )

        assert returned is mock_grib
        assert mock_grib.keys["gridDefinitionTemplateNumber"] == 40
        assert mock_grib.keys["latitudeOfFirstGridPoint"] == int(-60.0e6)
        assert mock_grib.keys["latitudeOfLastGridPoint"] == int(60.0e6)
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

    def test_writes_decreasing_lon_endpoints(self, mock_grib, patched_eccodes):
        cube = make_gaussian_cube(
            x_points=[270.0, 180.0, 90.0, 0.0] * 4,
            y_points=[-60.0] * 4 + [-30.0] * 4 + [30.0] * 4 + [60.0] * 4,
        )
        save_rules.grid_definition_template_40(
            cube, mock_grib, cube.coord("longitude"), cube.coord("latitude")
        )
        assert mock_grib.keys["longitudeOfFirstGridPoint"] == int(270.0e6)
        assert mock_grib.keys["longitudeOfLastGridPoint"] == int(0.0e6)

    def test_writes_decreasing_lat_endpoints(self, mock_grib, patched_eccodes):
        cube = make_gaussian_cube(
            x_points=[0.0, 90.0, 180.0, 270.0] * 4,
            y_points=[60.0] * 4 + [30.0] * 4 + [-30.0] * 4 + [-60.0] * 4,
        )
        save_rules.grid_definition_template_40(
            cube, mock_grib, cube.coord("longitude"), cube.coord("latitude")
        )
        assert mock_grib.keys["latitudeOfFirstGridPoint"] == int(60.0e6)
        assert mock_grib.keys["latitudeOfLastGridPoint"] == int(-60.0e6)

    def test_writes_pl_with_varying_lon_counts(self, mock_grib, patched_eccodes):
        cube = make_gaussian_cube(
            x_points=[0.0, 180.0, 0.0, 90.0, 180.0, 270.0],
            y_points=[-60.0, -60.0, 60.0, 60.0, 60.0, 60.0],
        )
        save_rules.grid_definition_template_40(
            cube, mock_grib, cube.coord("longitude"), cube.coord("latitude")
        )
        assert mock_grib.keys["N"] == 1
        assert mock_grib.keys["Nj"] == 2
        assert mock_grib.keys["pl"] == [2, 4]
