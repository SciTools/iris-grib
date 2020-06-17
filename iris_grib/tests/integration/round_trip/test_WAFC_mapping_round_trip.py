# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration test for round-trip loading and saving of hybrid height and
hybrid pressure cubes.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris import load_cube, load, save
from iris.cube import Cube


@tests.skip_grib_data
class TestWAFCCodes(tests.IrisGribTest):
    def setUp(self):
        self.cat = self.get_testdata_path('CAT_T+24_0600.grib2')
        self.cb = self.get_testdata_path('CB_T+24_0600.grib2')
        self.icing = self.get_testdata_path('ICING_T+24_0600.grib2')
        self.turb = self.get_testdata_path('INCLDTURB_T+24_0600.grib2')

    def test_WAFC_CAT_round_trip(self):
        cubelist = load(self.cat, 'WAFC_CAT_potential')
        cube = cubelist[0]
        self.assertIsInstance(cube, Cube)

        with self.temp_filename() as tmp_save_path:
            save(cube, tmp_save_path, saver='grib2')
            saved_cube = load_cube(tmp_save_path)
            self.assertEqual(saved_cube.metadata, cube.metadata)

    def test_WAFC_CB_round_trip(self):
        cubelist = load(self.cb)
        cube = cubelist[0]
        self.assertIsInstance(cube, Cube)

        with self.temp_filename() as tmp_save_path:
            save(cube, tmp_save_path, saver='grib2')
            saved_cube = load_cube(tmp_save_path)
            self.assertEqual(saved_cube.metadata, cube.metadata)

    def test_WAFC_icing_round_trip(self):
        cubelist = load(self.icing)
        cube = cubelist[0]
        self.assertIsInstance(cube, Cube)

        with self.temp_filename() as tmp_save_path:
            save(cube, tmp_save_path, saver='grib2')
            saved_cube = load_cube(tmp_save_path)
            self.assertEqual(saved_cube.metadata, cube.metadata)

    def test_WAFC_turb_round_trip(self):
        cubelist = load(self.turb)
        cube = cubelist[0]
        self.assertIsInstance(cube, Cube)

        with self.temp_filename() as tmp_save_path:
            save(cube, tmp_save_path, saver='grib2')
            saved_cube = load_cube(tmp_save_path)
            self.assertEqual(saved_cube.metadata, cube.metadata)


if __name__ == '__main__':
    tests.main()
