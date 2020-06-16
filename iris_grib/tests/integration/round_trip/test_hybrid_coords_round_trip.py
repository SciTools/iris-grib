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

from iris import load_cube, load_cubes, save
# Try except allows compatibility with current Iris (2.4) and also master.
# TODO: simplify to just the iris.util import once we drop support for any
# Iris versions with iris.experimental.equalise_cubes import
try:
    from iris.util import equalise_attributes
except ImportError:
    from iris.experimental.equalise_cubes import equalise_attributes


@tests.skip_grib_data
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


@tests.skip_grib_data
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
