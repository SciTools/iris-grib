# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Unit tests for module-level functions."""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import iris

from iris_grib._save_rules import _non_missing_forecast_period


class Test(tests.IrisGribTest):
    def _cube(self, t_bounds=False):
        time_coord = iris.coords.DimCoord(15, standard_name='time',
                                          units='hours since epoch')
        fp_coord = iris.coords.DimCoord(10, standard_name='forecast_period',
                                        units='hours')
        if t_bounds:
            time_coord.bounds = [[8, 100]]
            fp_coord.bounds = [[3, 95]]
        cube = iris.cube.Cube([23])
        cube.add_dim_coord(time_coord, 0)
        cube.add_aux_coord(fp_coord, 0)
        return cube

    def test_time_point(self):
        cube = self._cube()
        rt, rt_meaning, fp, fp_meaning = _non_missing_forecast_period(cube)
        self.assertEqual((rt_meaning, fp, fp_meaning), (1, 10, 1))

    def test_time_bounds(self):
        cube = self._cube(t_bounds=True)
        rt, rt_meaning, fp, fp_meaning = _non_missing_forecast_period(cube)
        self.assertEqual((rt_meaning, fp, fp_meaning), (1, 3, 1))

    def test_time_bounds_in_minutes(self):
        cube = self._cube(t_bounds=True)
        cube.coord('forecast_period').convert_units('minutes')
        rt, rt_meaning, fp, fp_meaning = _non_missing_forecast_period(cube)
        self.assertEqual((rt_meaning, fp, fp_meaning), (1, 180, 0))


if __name__ == "__main__":
    tests.main()
