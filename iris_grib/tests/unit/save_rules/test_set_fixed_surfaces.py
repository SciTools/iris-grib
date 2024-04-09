# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.set_fixed_surfaces`.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

import eccodes
from eccodes import CODES_MISSING_LONG as GRIB_MISSING_LONG
import numpy as np

import iris.cube
import iris.coords
from iris.exceptions import TranslationError

from iris_grib._save_rules import set_fixed_surfaces


class Test(tests.IrisGribTest):
    def test_bounded_altitude_feet(self):
        cube = iris.cube.Cube([0])
        cube.add_aux_coord(iris.coords.AuxCoord(
            1500.0, long_name='altitude', units='ft',
            bounds=np.array([1000.0, 2000.0])))
        grib = eccodes.codes_grib_new_from_samples("GRIB2")
        set_fixed_surfaces(cube, grib)
        self.assertEqual(
            eccodes.codes_get_double(grib, "scaledValueOfFirstFixedSurface"),
            305.0)  # precise ~304.8
        self.assertEqual(
            eccodes.codes_get_double(grib, "scaledValueOfSecondFixedSurface"),
            610.0)  # precise ~609.6
        self.assertEqual(
            eccodes.codes_get_long(grib, "typeOfFirstFixedSurface"),
            102)
        self.assertEqual(
            eccodes.codes_get_long(grib, "typeOfSecondFixedSurface"),
            102)

    def test_theta_level(self):
        cube = iris.cube.Cube([0])
        cube.add_aux_coord(iris.coords.AuxCoord(
            230.0, standard_name='air_potential_temperature',
            units='K', attributes={'positive': 'up'},
            bounds=np.array([220.0, 240.0])))
        grib = eccodes.codes_grib_new_from_samples("GRIB2")
        set_fixed_surfaces(cube, grib)
        self.assertEqual(
            eccodes.codes_get_double(grib, "scaledValueOfFirstFixedSurface"),
            220.0)
        self.assertEqual(
            eccodes.codes_get_double(grib, "scaledValueOfSecondFixedSurface"),
            240.0)
        self.assertEqual(
            eccodes.codes_get_long(grib, "typeOfFirstFixedSurface"),
            107)
        self.assertEqual(
            eccodes.codes_get_long(grib, "typeOfSecondFixedSurface"),
            107)

    def test_depth(self):
        cube = iris.cube.Cube([0])
        cube.add_aux_coord(iris.coords.AuxCoord(
            1, long_name='depth', units='m',
            bounds=np.array([0., 2]), attributes={'positive': 'down'}))
        grib = eccodes.codes_grib_new_from_samples("GRIB2")
        set_fixed_surfaces(cube, grib)
        self.assertEqual(
            eccodes.codes_get_double(grib, "scaledValueOfFirstFixedSurface"),
            0.)
        self.assertEqual(
            eccodes.codes_get_double(grib, "scaledValueOfSecondFixedSurface"),
            2)
        self.assertEqual(
            eccodes.codes_get_long(grib, "typeOfFirstFixedSurface"),
            106)
        self.assertEqual(
            eccodes.codes_get_long(grib, "typeOfSecondFixedSurface"),
            106)

    @mock.patch.object(eccodes, "codes_set")
    def test_altitude_point(self, mock_set):
        grib = None
        cube = iris.cube.Cube([1, 2, 3, 4, 5])
        cube.add_aux_coord(
            iris.coords.AuxCoord([12345], "altitude", units="m")
        )

        set_fixed_surfaces(cube, grib)

        mock_set.assert_any_call(grib, "typeOfFirstFixedSurface", 102)
        mock_set.assert_any_call(grib, "scaleFactorOfFirstFixedSurface", 0)
        mock_set.assert_any_call(grib, "scaledValueOfFirstFixedSurface",
                                 12345)
        mock_set.assert_any_call(grib, "typeOfSecondFixedSurface", 255)
        mock_set.assert_any_call(grib, "scaleFactorOfSecondFixedSurface",
                                 GRIB_MISSING_LONG)
        mock_set.assert_any_call(grib, "scaledValueOfSecondFixedSurface",
                                 GRIB_MISSING_LONG)

    @mock.patch.object(eccodes, "codes_set")
    def test_height_point(self, mock_set):
        grib = None
        cube = iris.cube.Cube([1, 2, 3, 4, 5])
        cube.add_aux_coord(iris.coords.AuxCoord([12345], "height", units="m"))

        set_fixed_surfaces(cube, grib)

        mock_set.assert_any_call(grib, "typeOfFirstFixedSurface", 103)
        mock_set.assert_any_call(grib, "scaleFactorOfFirstFixedSurface", 0)
        mock_set.assert_any_call(grib, "scaledValueOfFirstFixedSurface", 12345)
        mock_set.assert_any_call(grib, "typeOfSecondFixedSurface", 255)
        mock_set.assert_any_call(grib, "scaleFactorOfSecondFixedSurface",
                                 GRIB_MISSING_LONG)
        mock_set.assert_any_call(grib, "scaledValueOfSecondFixedSurface",
                                 GRIB_MISSING_LONG)

    def test_unknown_vertical_unbounded(self):
        cube = iris.cube.Cube([0])
        cube.add_aux_coord(
            iris.coords.AuxCoord([1],
                                 attributes={'GRIB_fixed_surface_type': 151}))
        grib = eccodes.codes_grib_new_from_samples("GRIB2")
        set_fixed_surfaces(cube, grib)

        self.assertEqual(eccodes.codes_get_long(
            grib, "typeOfFirstFixedSurface"), 151)
        self.assertEqual(eccodes.codes_get_double(
            grib, "scaledValueOfFirstFixedSurface"), 1)
        self.assertEqual(eccodes.codes_get_double(
            grib, "scaleFactorOfFirstFixedSurface"), 0)
        self.assertEqual(eccodes.codes_get_long(
            grib, "typeOfSecondFixedSurface"), 255)
        self.assertEqual(eccodes.codes_get_long(
            grib, "scaledValueOfSecondFixedSurface"), GRIB_MISSING_LONG)
        self.assertEqual(eccodes.codes_get_long(
            grib, "scaleFactorOfSecondFixedSurface"), GRIB_MISSING_LONG)

    def test_unknown_vertical_bounded(self):
        cube = iris.cube.Cube([0])
        cube.add_aux_coord(
            iris.coords.AuxCoord([700], bounds=np.array([900.0, 500.0]),
                                 attributes={'GRIB_fixed_surface_type': 108}))
        grib = eccodes.codes_grib_new_from_samples("GRIB2")
        set_fixed_surfaces(cube, grib)

        self.assertEqual(
            eccodes.codes_get_long(grib, "typeOfFirstFixedSurface"), 108)
        self.assertEqual(
            eccodes.codes_get_double(grib, "scaledValueOfFirstFixedSurface"),
            900)
        self.assertEqual(
            eccodes.codes_get_double(grib, "scaleFactorOfFirstFixedSurface"),
            0)
        self.assertEqual(
            eccodes.codes_get_long(grib, "typeOfSecondFixedSurface"), 108)
        self.assertEqual(
            eccodes.codes_get_long(grib, "scaledValueOfSecondFixedSurface"),
            500)
        self.assertEqual(
            eccodes.codes_get_long(grib, "scaleFactorOfSecondFixedSurface"),
            0)

    def test_multiple_unknown_vertical_coords(self):
        grib = None
        cube = iris.cube.Cube([0])
        cube.add_aux_coord(
            iris.coords.AuxCoord([1],
                                 attributes={'GRIB_fixed_surface_type': 151}))
        cube.add_aux_coord(
            iris.coords.AuxCoord([450], bounds=np.array([900.0, 0.0]),
                                 attributes={'GRIB_fixed_surface_type': 108}))
        msg = r"coordinates were found of fixed surface type: \[151, 108\]"
        with self.assertRaisesRegex(ValueError, msg):
            set_fixed_surfaces(cube, grib)

    def test_unhandled_vertical_axis(self):
        grib = None
        cube = iris.cube.Cube([0])
        cube.add_aux_coord(
            iris.coords.AuxCoord([450], attributes={'positive': 'up'}))
        msg = r"vertical-axis coordinate\(s\) \('unknown'\) are not " \
              "recognised or handled."
        with self.assertRaisesRegex(TranslationError, msg):
            set_fixed_surfaces(cube, grib)

    @mock.patch.object(eccodes, "codes_set")
    def test_no_vertical(self, mock_set):
        grib = None
        cube = iris.cube.Cube([1, 2, 3, 4, 5])
        set_fixed_surfaces(cube, grib)
        mock_set.assert_any_call(grib, "typeOfFirstFixedSurface", 1)
        mock_set.assert_any_call(grib, "scaleFactorOfFirstFixedSurface", 0)
        mock_set.assert_any_call(grib, "scaledValueOfFirstFixedSurface", 0)
        mock_set.assert_any_call(grib, "typeOfSecondFixedSurface", 255)
        mock_set.assert_any_call(grib, "scaleFactorOfSecondFixedSurface",
                                 GRIB_MISSING_LONG)
        mock_set.assert_any_call(grib, "scaledValueOfSecondFixedSurface",
                                 GRIB_MISSING_LONG)


if __name__ == "__main__":
    tests.main()
