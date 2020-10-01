# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration tests to confirm data is loaded correctly.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import numpy.ma as ma

from iris import load_cube


class TestImport(tests.IrisGribTest):
    def test_gdt1(self):
        path = tests.get_data_path(
            ("GRIB", "rotated_nae_t", "sensible_pole.grib2")
        )
        cube = load_cube(path)
        self.assertCMLApproxData(cube)

    def test_gdt90_with_bitmap(self):
        path = tests.get_data_path(("GRIB", "umukv", "ukv_chan9.grib2"))
        cube = load_cube(path)
        # Pay particular attention to the orientation.
        self.assertIsNot(cube.data[0, 0], ma.masked)
        self.assertIs(cube.data[-1, 0], ma.masked)
        self.assertIs(cube.data[0, -1], ma.masked)
        self.assertIs(cube.data[-1, -1], ma.masked)
        x = cube.coord("projection_x_coordinate").points
        y = cube.coord("projection_y_coordinate").points
        self.assertGreater(x[0], x[-1])  # Decreasing X coordinate
        self.assertLess(y[0], y[-1])  # Increasing Y coordinate
        # Check everything else.
        self.assertCMLApproxData(cube)


class TestGDT30(tests.IrisGribTest):
    def test_lambert(self):
        path = tests.get_data_path(("GRIB", "lambert", "lambert.grib2"))
        cube = load_cube(path)
        self.assertCMLApproxData(cube)

    def test_context(self):
        import os
        import sys
        import iris.coord_systems as ics
        iris_lc = ics.LambertConformal(false_easting=0)
        iris_lc_param = iris_lc.false_easting
        iris_lc_fe="{paramtype}({value})".format(
            value=iris_lc_param,
            paramtype=type(iris_lc_param))
        msg = (
            "\n\n"
            "PYTHON INSTALL CONTEXT for coord-systems:\n"
            "python os path:  {os_path!s}\n"
            "python sys version:\n{sys_version!s}\n"
            "iris coord-systems path:  {iris_cs_path!s}\n"
            "iris coord-systems '_arg_default':  {iris_cs_argdef!r}\n"
            "iris LambertConformal default false_easting:  {iris_lc_fe!r}\n"
            )
        kwargs = dict(
            os_path=os.__file__,
            sys_version=sys.version,
            iris_cs_path=ics.__file__,
            iris_cs_argdef=getattr(ics, "_arg_default", None),
            iris_lc_fe=iris_lc_fe
            )
        msg = msg.format(**kwargs)
        self.assertEqual(1, 0, msg)


class TestGDT40(tests.IrisGribTest):
    def test_regular(self):
        path = tests.get_data_path(("GRIB", "gaussian", "regular_gg.grib2"))
        cube = load_cube(path)
        self.assertCMLApproxData(cube)

    def test_reduced(self):
        path = tests.get_data_path(("GRIB", "reduced", "reduced_gg.grib2"))
        cube = load_cube(path)
        self.assertCMLApproxData(cube)


class TestDRT3(tests.IrisGribTest):
    def test_grid_complex_spatial_differencing(self):
        path = tests.get_data_path(
            ("GRIB", "missing_values", "missing_values.grib2")
        )
        cube = load_cube(path)
        self.assertCMLApproxData(cube)


if __name__ == '__main__':
    tests.main()
