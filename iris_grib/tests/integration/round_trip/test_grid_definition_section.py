# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Integration test for round-trip loading and saving of various grids.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from typing import Literal

import numpy as np

from iris import load_cube, save
from iris.coord_systems import (
    GeogCS,
    PolarStereographic,
    RotatedGeogCS,
    Stereographic
)
from iris.coords import DimCoord
from iris.cube import Cube
from iris.fileformats.pp import EARTH_RADIUS as UM_DEFAULT_EARTH_RADIUS
from iris.util import is_regular

from iris_grib.grib_phenom_translation import GRIBCode


class TestGDT5(tests.TestGribMessage):
    def test_save_load(self):
        # Load sample UKV data (variable-resolution rotated grid).
        path = tests.get_data_path(("PP", "ukV1", "ukVpmslont.pp"))
        cube = load_cube(path)

        # Extract a single 2D field, for simplicity.
        self.assertEqual(cube.ndim, 3)
        self.assertEqual(cube.coord_dims("time"), (0,))
        cube = cube[0]

        # Check that it has a rotated-pole variable-spaced grid, as expected.
        x_coord = cube.coord(axis="x")
        self.assertIsInstance(x_coord.coord_system, RotatedGeogCS)
        self.assertFalse(is_regular(x_coord))

        # Write to temporary file, check that key contents are in the file,
        # then load back in.
        with self.temp_filename("ukv_sample.grib2") as temp_file_path:
            save(cube, temp_file_path)

            # Check that various aspects of the saved file are as expected.
            expect_values = (
                (0, "editionNumber", 2),
                (3, "gridDefinitionTemplateNumber", 5),
                (3, "Ni", cube.shape[-1]),
                (3, "Nj", cube.shape[-2]),
                (3, "shapeOfTheEarth", 1),
                (
                    3,
                    "scaledValueOfRadiusOfSphericalEarth",
                    int(UM_DEFAULT_EARTH_RADIUS),
                ),
                (3, "resolutionAndComponentFlags", 0),
                (3, "latitudeOfSouthernPole", -37500000),
                (3, "longitudeOfSouthernPole", 357500000),
                (3, "angleOfRotation", 0),
            )
            self.assertGribMessageContents(temp_file_path, expect_values)

            # Load the Grib file back into a new cube.
            cube_loaded_from_saved = load_cube(temp_file_path)
            # Also load data, before the temporary file gets deleted.
            cube_loaded_from_saved.data

        # The re-loaded result will not match the original in every respect:
        #  * cube attributes are discarded
        #  * horizontal coordinates are rounded to an integer representation
        #  * bounds on horizontal coords are lost
        # Thus the following "equivalence tests" are rather piecemeal..

        # Check those re-loaded properties which should match the original.
        for test_cube in (cube, cube_loaded_from_saved):
            self.assertEqual(
                test_cube.standard_name, "air_pressure_at_sea_level"
            )
            self.assertEqual(test_cube.units, "Pa")
            self.assertEqual(test_cube.shape, (928, 744))
            self.assertEqual(test_cube.cell_methods, ())

        # Check only the GRIB_PARAM attribute exists on the re-loaded cube.
        # Note: this does *not* match the original, but is as expected.
        self.assertEqual(
            cube_loaded_from_saved.attributes,
            {"GRIB_PARAM": GRIBCode("GRIB2:d000c003n001")},
        )

        # Now remaining to check: coordinates + data...

        # Check they have all the same coordinates.
        co_names = [coord.name() for coord in cube.coords()]
        co_names_reload = [
            coord.name() for coord in cube_loaded_from_saved.coords()
        ]
        self.assertEqual(sorted(co_names_reload), sorted(co_names))

        # Check all the coordinates.
        for coord_name in co_names:
            try:
                co_orig = cube.coord(coord_name)
                co_load = cube_loaded_from_saved.coord(coord_name)

                # Check shape.
                self.assertEqual(
                    co_load.shape,
                    co_orig.shape,
                    'Shape of re-loaded "{}" coord is {} '
                    "instead of {}".format(
                        coord_name, co_load.shape, co_orig.shape
                    ),
                )

                # Check coordinate points equal, within a tolerance.
                self.assertArrayAllClose(
                    co_load.points, co_orig.points, rtol=1.0e-6
                )

                # Check all coords are unbounded.
                # (NOTE: this is not so for the original X and Y coordinates,
                # but Grib does not store those bounds).
                self.assertIsNone(co_load.bounds)

            except AssertionError as err:
                self.assertTrue(
                    False,
                    'Failed on coordinate "{}" : {}'.format(
                        coord_name, str(err)
                    ),
                )

        # Check that main data array also matches.
        self.assertArrayAllClose(cube.data, cube_loaded_from_saved.data)


class GDT20Common(tests.TestGribMessage):
    """Roundtrip testing that GDT20 will save+load all attributes correctly."""

    # Enable subclassing to test different permutations.
    coord_system_class: type[Stereographic] = NotImplemented
    pole: Literal["north", "south"] = NotImplemented

    def setUp(self):
        # Create a Cube to save, inspired by
        #  iris-sample-data toa_brightness_stereographic.nc
        if self.pole == "north":
            central_lat = 90
        elif self.pole == "south":
            central_lat = -90
        else:
            raise NotImplementedError(f"Invalid pole: {self.pole}")

        self.coord_system_kwargs = dict(
            central_lat=central_lat,
            central_lon=325,
            true_scale_lat=central_lat,
            ellipsoid=GeogCS(6378169.0),
        )
        coord_system = self.coord_system_class(**self.coord_system_kwargs)

        coord_kwargs = dict(
            units="m",
            coord_system=coord_system,
        )
        coord_x = DimCoord(
            np.linspace(-2250000, 6750192, 256, endpoint=False),
            standard_name="projection_x_coordinate",
            **coord_kwargs
        )
        coord_y = DimCoord(
            np.linspace(-980000, -6600000, 160, endpoint=False),
            standard_name="projection_y_coordinate",
            **coord_kwargs
        )
        coord_t = DimCoord(
            0,
            standard_name="time",
            units="hours since 1970-01-01 00:00:00"
        )
        coord_fp = DimCoord(0, standard_name="forecast_period", units="hours")
        coord_frt = DimCoord(
            0,
            standard_name="forecast_reference_time",
            units=coord_t.units
        )
        cube_shape = (coord_y.shape[0], coord_x.shape[0])
        self.cube = Cube(
            np.arange(np.prod(cube_shape), dtype=float).reshape(cube_shape),
            dim_coords_and_dims=[(coord_y, 0), (coord_x, 1)],
            aux_coords_and_dims=[
                (coord_t, None),
                (coord_fp, None),
                (coord_frt, None)
            ],
        )

    def test_save_load(self):
        with self.temp_filename("polar_stereo.grib2") as temp_file_path:
            save(self.cube, temp_file_path)
            cube_reloaded = load_cube(temp_file_path)
            # Touch the data before destroying the file.
            _ = cube_reloaded.data

        cube_expected = self.cube.copy()
        for coord in cube_expected.dim_coords:
            # GRIB only describes PolarStereographic, so we always expect that
            #  system even when we started with Stereographic.
            coord.coord_system = PolarStereographic(**self.coord_system_kwargs)

        # Modifications to remove irrelevant inequalities.
        del cube_reloaded.attributes["GRIB_PARAM"]
        for coord in cube_reloaded.dim_coords:
            coord.points = np.round(coord.points)

        self.assertEqual(cube_expected, cube_reloaded)


class TestGDT20StereoNorth(GDT20Common):
    coord_system_class = Stereographic
    pole = "north"


class TestGDT20StereoSouth(GDT20Common):
    coord_system_class = Stereographic
    pole = "south"


class TestGDT20PolarNorth(GDT20Common):
    coord_system_class = PolarStereographic
    pole = "north"


class TestGDT20PolarSouth(GDT20Common):
    coord_system_class = PolarStereographic
    pole = "south"


if __name__ == "__main__":
    tests.main()
