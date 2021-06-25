# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration test for loading hybrid height data.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests


from iris import load_cube
from iris.aux_factory import HybridHeightFactory, HybridPressureFactory


@tests.skip_grib_data
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
        self.assertArrayAllClose(cube.coord('sigma').points,
                                 [0.998, 0.894, 0.667],
                                 atol=0.001)

        # check height values too.
        self.assertArrayAllClose(cube.coord('level_height').points,
                                 [20., 953.3,  3220.],
                                 atol=0.5)


@tests.skip_grib_data
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
                                 [0., 0.045, 1.], atol=0.001)
        self.assertArrayAllClose(cube.coord('level_pressure').points,
                                 [2.00004, 18716.9688, 0.], rtol=0.0001)
        self.assertArrayAllClose(
            cube.coord('surface_air_pressure')[:2, :3].points,
            [[103493.8, 103493.8, 103493.8],
             [103401.0, 103407.4, 103412.2]], atol=0.1)

        # Also check a few values from the derived coord.
        self.assertArrayAllClose(
            cube.coord('air_pressure')[:, :3, 0].points,
            [[2., 2., 2.],
             [23389.3, 23385.1, 23379.9],
             [103493.8, 103401.0, 103285.8]], atol=0.1)


if __name__ == '__main__':
    tests.main()
