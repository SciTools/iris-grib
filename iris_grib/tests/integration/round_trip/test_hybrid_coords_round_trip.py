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

from iris import load_cube, load_cubes, save
from iris.experimental.equalise_cubes import equalise_attributes


class TestHybridHeightRoundTrip(tests.IrisGribTest):
    def test_hh_round_trip(self):
        filepath = self.get_testdata_path(
            'faked_sample_hh_grib_data.grib2')
        # Load and save temperature cube and reference (orography) cube
        # separately because this is the only way to save the hybrid height
        # coordinate.
        cube, ref_cube = load_cubes(filepath,
                                    ('air_temperature', 'surface_altitude'))

        with self.temp_filename() as tmp_save_path:
            save([cube, ref_cube], tmp_save_path, saver='grib2')
            # Only need to reload temperature cube to compare with unsaved
            # temperature cube.
            saved_cube = load_cube(tmp_save_path, 'air_temperature')
            self.assertTrue(saved_cube == cube)


class TestHybridPressureRoundTrip(tests.IrisGribTest):
    def test_hybrid_pressure(self):
        filepath = self.get_testdata_path(
            'faked_sample_hp_grib_data.grib2')
        # Load and save temperature cube and reference (air_pressure at
        # surface) cube separately because this is the only way to save the
        # hybrid pressure coordinate.
        cube, ref_cube = load_cubes(filepath,
                                    ('air_temperature', 'air_pressure'))

        with self.temp_filename() as tmp_save_path:
            save([cube, ref_cube], tmp_save_path, saver='grib2')
            # Only need to reload temperature cube to compare with unsaved
            # temperature cube.
            saved_cube = load_cube(tmp_save_path, 'air_temperature')

            # Currently all attributes are lost when saving to grib, so we must
            # equalise them in order to successfully compare all other aspects.
            equalise_attributes([saved_cube, cube])

            self.assertTrue(saved_cube == cube)


if __name__ == '__main__':
    tests.main()
