# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration tests for loading various production definitions.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests


from iris import load_cube


class TestPDT8(tests.IrisGribTest):
    def setUp(self):
        # Load from the test file.
        file_path = tests.get_data_path(
            ("GRIB", "time_processed", "time_bound.grib2")
        )
        self.cube = load_cube(file_path)

    def test_coords(self):
        # Check the result has main coordinates as expected.
        for name, shape, is_bounded in [
            ("forecast_reference_time", (1,), False),
            ("time", (1,), True),
            ("forecast_period", (1,), True),
            ("pressure", (1,), False),
            ("latitude", (73,), False),
            ("longitude", (96,), False),
        ]:
            coords = self.cube.coords(name)
            self.assertEqual(
                len(coords),
                1,
                "expected one {!r} coord, found {}".format(name, len(coords)),
            )
            (coord,) = coords
            self.assertEqual(
                coord.shape,
                shape,
                "coord {!r} shape is {} instead of {!r}.".format(
                    name, coord.shape, shape
                ),
            )
            self.assertEqual(
                coord.has_bounds(),
                is_bounded,
                "coord {!r} has_bounds={}, expected {}.".format(
                    name, coord.has_bounds(), is_bounded
                ),
            )

    def test_cell_method(self):
        # Check the result has the expected cell method.
        cell_methods = self.cube.cell_methods
        self.assertEqual(
            len(cell_methods),
            1,
            "result has {} cell methods, expected one.".format(
                len(cell_methods)
            ),
        )
        (cell_method,) = cell_methods
        self.assertEqual(cell_method.coord_names, ("time",))


if __name__ == "__main__":
    tests.main()
