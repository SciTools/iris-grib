# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration test for round-trip loading and saving of various grids.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris import load_cube, save
from iris.coord_systems import RotatedGeogCS
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


if __name__ == "__main__":
    tests.main()
