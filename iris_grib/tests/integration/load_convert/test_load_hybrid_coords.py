# (C) British Crown Copyright 2018, Met Office
#
# This file is part of iris-grib.
#
# iris-grib is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-grib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-grib.  If not, see <http://www.gnu.org/licenses/>.
"""
Integration test for loading hybrid height data.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests


from iris import load_cube, load
from iris.aux_factory import HybridHeightFactory, HybridPressureFactory


class TestHybridHeight(tests.IrisGribTest):
    def setUp(self):
        filepath = self.get_testdata_path('faked_sample_hh_grib_data.grib2')
        self.testdata_cube = load_cube(filepath, 'air_temperature')

    def test_load_hybrid_height(self):
        # Check that it loads right, and creates a factory.
        self.assertIsInstance(self.testdata_cube.aux_factories[0],
                              HybridHeightFactory)

    def test_hybrid_height_coords_values(self):
        cube = self.testdata_cube

        # check actual model level values.
        self.assertArrayEqual(cube.coord('model_level_number').points,
                              [1, 11, 21])

        # check sigma values correctly loaded from indices 1, 11, 21.
        # NOTE: level[0] == 1, so sigma[0] == 1.0 :  This makes sense !
        self.assertArrayAllClose(cube.coord('sigma').points,
                                 [1.0, 0.911, 0.694],
                                 atol=0.001)

        # check height values too.
        self.assertArrayAllClose(cube.coord('level_height').points,
                                 [0., 800.,  2933.],
                                 atol=0.5)


class TestHybridPressure(tests.IrisGribTest):
    def setUp(self):
        filepath = self.get_testdata_path('faked_sample_hp_grib_data.grib2')
        self.testdata_cube = load_cube(filepath, 'air_temperature')

    def test_load_hybrid_pressure(self):
        # Check that it loads right, and creates a factory.
        self.assertIsInstance(self.testdata_cube.aux_factories[0],
                              HybridPressureFactory)

    def test_hybrid_pressure_coords_values(self):
        cube = self.testdata_cube

        # Check existence, and some values, of the loaded coefficients.
        self.assertArrayEqual(cube.coord('model_level_number').points,
                              [1, 51, 91])
        self.assertArrayAllClose(cube.coord('sigma').points,
                                 [0., 0.036, 0.998], atol=0.001)
        self.assertArrayAllClose(cube.coord('level_pressure').points,
                                 [0., 18191.0, 0.00316], rtol=0.001)
        self.assertArrayAllClose(
            cube.coord('surface_air_pressure')[:2, :3].points,
            [[103493.8, 103493.8, 103493.8],
             [103401.0, 103407.4, 103412.2]], atol=0.1)

        # Also check a few values from the derived coord.
        self.assertArrayAllClose(
            cube.coord('air_pressure')[:, :3, 0].points,
            [[0., 0., 0.],
             [21940.3, 21936.9, 21932.8],
             [103248.5, 103156.0, 103041.0]], atol=0.1)


if __name__ == '__main__':
    tests.main()
