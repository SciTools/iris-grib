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


from iris import load_cube
from iris.aux_factory import HybridHeightFactory, HybridPressureFactory


class TestHybridHeight(tests.IrisGribTest):
    def test_load_hybrid_height(self):
        filepath = self.get_testdata_path('faked_sample_hh_grib_data.grib2')
        cube = load_cube(filepath, 'air_temperature')
        # Check that it loads right, and creates a factory.
        self.assertIsInstance(cube.aux_factories[0], HybridHeightFactory)

    def test_levels_values(self):
        filepath = self.get_testdata_path('faked_sample_hh_grib_data.grib2')
        cube = load_cube(filepath, 'air_temperature')

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
    def test_load_hybrid_pressure(self):
        filepath = self.get_testdata_path('faked_sample_hp_grib_data.grib2')
        cube = load_cube(filepath, 'air_pressure')
        # cubes = load(filepath)
        # print(cube)
        # Check that it loads right, and creates a factory.
        self.assertIsInstance(cube.aux_factories[0], HybridPressureFactory)

if __name__ == '__main__':
    tests.main()
