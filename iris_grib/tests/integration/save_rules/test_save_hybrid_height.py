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
Unit tests for :func:`iris_grib._save_rules.data_section`.

"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised before
# importing anything else
import iris_grib.tests as tests

import iris
from iris.cube import Cube

from iris_grib import save_pairs_from_cube, save_messages, GribMessage


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
                [5., 0, 45., 0, 111.667, 0,
                 0.999, 0, 0.995, 0, 0.987, 0],
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


if __name__ == '__main__':
    tests.main()
