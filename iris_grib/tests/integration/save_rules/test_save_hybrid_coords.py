# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.data_section`.

"""

# import iris_grib.tests first so that some things can be initialised before
# importing anything else
import iris_grib.tests as tests

import numpy as np

import iris

from iris_grib import save_pairs_from_cube, save_messages, GribMessage


@tests.skip_grib_data
class TestSaveHybridHeight(tests.IrisGribTest):
    def setUp(self):
        reference_data_filepath = self.get_testdata_path('hybrid_height.nc')
        if (hasattr(iris.FUTURE, 'netcdf_promote') and
                not iris.FUTURE.netcdf_promote):
            iris.FUTURE.netcdf_promote = True
        data_cube = iris.load_cube(reference_data_filepath,
                                   'air_potential_temperature')
        # Use only 3 (non-contiguous) levels, and a single timestep.
        data_cube = data_cube[0, :6:2]
        self.test_hh_data_cube = data_cube

    def test_save(self):
        # Get save-pairs for the test data.
        save_pairs = save_pairs_from_cube(self.test_hh_data_cube)

        # Check there are 3 of them (and nothing failed !)
        save_pairs = list(save_pairs)
        self.assertEqual(len(save_pairs), 3)

        # Get a list of just the messages.
        msgs = [pair[1] for pair in save_pairs]

        # Save the messages to a temporary file.
        with self.temp_filename() as temp_path:
            save_messages(msgs, temp_path, append=True)

            # Read back as GribMessage-s.
            msgs = list(GribMessage.messages_from_filename(temp_path))

            # Check 3 messages were saved.
            self.assertEqual(len(msgs), 3)

            # Check that the PV vector (same in all messages) is as expected.
            # Note: gaps here are because we took model levels = (1, 3, 5).
            self.assertArrayAllClose(
                msgs[0].sections[4]['pv'],
                [0, 5., 0, 45., 0, 111.667, 0, 0.999, 0, 0.995, 0, 0.987],
                atol=0.0015)

            # Check message #2-of-3 has the correctly encoded hybrid height.
            msg = msgs[1]
            #  first surface type = 118  (i.e. hybrid height).
            self.assertEqual(
                msg.sections[4]['typeOfFirstFixedSurface'],
                118)
            #  first surface scaling = 0.
            self.assertEqual(
                msg.sections[4]['scaleFactorOfFirstFixedSurface'],
                0)
            #  first surface value = 3  -- i.e. #2 of (1, 3, 5).
            self.assertEqual(
                msg.sections[4]['scaledValueOfFirstFixedSurface'],
                3)
            #  second surface type = "NONE"  -- i.e. unbounded level.
            self.assertEqual(
                msg.sections[4]['typeOfSecondFixedSurface'],
                255)


@tests.skip_grib_data
class TestSaveHybridPressure(tests.IrisGribTest):
    def setUp(self):
        reference_data_filepath = self.get_testdata_path(
            'hybrid_pressure.nc')
        data_cube = iris.load_cube(reference_data_filepath,
                                   'air_temperature')
        self.test_hp_data_cube = data_cube

    def test_save(self):
        # Get save-pairs for the test data.
        save_pairs = save_pairs_from_cube(self.test_hp_data_cube)

        # Check there are 3 of them (and nothing failed !)
        save_pairs = list(save_pairs)
        self.assertEqual(len(save_pairs), 3)

        # Get a list of just the messages.
        msgs = [pair[1] for pair in save_pairs]

        # Save the messages to a temporary file.
        with self.temp_filename() as temp_path:
            save_messages(msgs, temp_path, append=True)

            # Read back as GribMessage-s.
            msgs = list(GribMessage.messages_from_filename(temp_path))

            # Check 3 messages were saved.
            self.assertEqual(len(msgs), 3)

            # Check that the PV vector (same in all messages) is as expected.
            # Note: HUGE gaps here because we took model levels = (1, 51, 91).
            self.assertEqual(msgs[0].sections[4]['NV'], 184)
            pv_expected = np.zeros(184, dtype=np.float64)
            pv_expected[[1, 51, 91]] = [0., 18191.03, 0.003]
            pv_expected[[93, 143, 183]] = [0., 0.036, 0.998]
            self.assertArrayAllClose(
                msgs[0].sections[4]['pv'], pv_expected, atol=0.001)

            # Check message #2-of-3 has the correctly encoded hybrid pressure.
            msg = msgs[1]
            #  first surface type = 119  (i.e. hybrid pressure).
            self.assertEqual(
                msg.sections[4]['typeOfFirstFixedSurface'],
                119)
            #  first surface scaling = 0.
            self.assertEqual(
                msg.sections[4]['scaleFactorOfFirstFixedSurface'],
                0)
            #  first surface value = 3  -- i.e. #2 of (1, 3, 5).
            self.assertEqual(
                msg.sections[4]['scaledValueOfFirstFixedSurface'],
                51)
            #  second surface type = "NONE"  -- i.e. unbounded level.
            self.assertEqual(
                msg.sections[4]['typeOfSecondFixedSurface'],
                255)


if __name__ == '__main__':
    tests.main()
