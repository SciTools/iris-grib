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
Integration test for round-trip loading and saving of hybrid height and
hybrid pressure cubes.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris import load_cube, load, save
from iris.cube import Cube


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
            self.assertTrue(saved_cube == cube)

    def test_WAFC_CB_round_trip(self):
        cubelist = load(self.cb)
        cube = cubelist[0]
        self.assertIsInstance(cube, Cube)

        with self.temp_filename() as tmp_save_path:
            save(cube, tmp_save_path, saver='grib2')
            saved_cube = load_cube(tmp_save_path)
            self.assertTrue(saved_cube == cube)

    def test_WAFC_icing_round_trip(self):
        cubelist = load(self.icing)
        cube = cubelist[0]
        self.assertIsInstance(cube, Cube)

        with self.temp_filename() as tmp_save_path:
            save(cube, tmp_save_path, saver='grib2')
            saved_cube = load_cube(tmp_save_path)
            self.assertTrue(saved_cube == cube)

    def test_WAFC_turb_round_trip(self):
        cubelist = load(self.turb)
        cube = cubelist[0]
        self.assertIsInstance(cube, Cube)

        with self.temp_filename() as tmp_save_path:
            save(cube, tmp_save_path, saver='grib2')
            saved_cube = load_cube(tmp_save_path)
            self.assertTrue(saved_cube == cube)


if __name__ == '__main__':
    tests.main()
