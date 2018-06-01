# (C) British Crown Copyright 2014 - 2017, Met Office
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
from iris import sample_data_path

from iris_grib import save_pairs_from_cube, save_messages, load_cubes


class TestSaveHybridHeight(tests.IrisGribTest):
    def setUp(self):
        reference_data_filepath = sample_data_path('hybrid_height.nc')
        if (hasattr(iris.FUTURE, 'netcdf_promote') and
                not iris.FUTURE.netcdf_promote):
            iris.FUTURE.netcdf_promote = True
        data_cube = iris.load_cube(reference_data_filepath,
                              'air_potential_temperature')
        # Only use 3 levels.
        data_cube = data_cube[:3]
        self.test_hh_data_cube = data_cube

        # Also make up a grib-saveable orography cube.
        # (look what a fuss this is !!)
        co_orog = data_cube.aux_factory().orography
        orog_cube = Cube(co_orog.points,
                         standard_name=co_orog.standard_name,
                         units=co_orog.units)
        for dim in range(2):
            orog_cube.add_dim_coord(data_cube[0].coord(dimensions=dim), dim)
        orog_cube.add_aux_coord(data_cube.coord('time'))
        self.test_orog_cube = orog_cube

    def test_roundtrip(self):
        # Get save-pairs for the test data.
        save_pairs = save_pairs_from_cube(self.test_hh_data_cube)
        # Check there are 3 of them (and nothing failed !)
        save_pairs = list(save_pairs)
        self.assertEqual(len(save_pairs), 3)
        # Also get save-pairs for the orography.
        orog_save_pairs = save_pairs_from_cube(self.test_orog_cube)
        # Get a list of just the messages.
        msgs = [pair[1] for pair in save_pairs]
        msgs.append(next(orog_save_pairs)[1])
        # Save the messages to a temporary file.
        with self.temp_filename() as temp_path:
            save_messages(msgs, temp_path, append=True)

            # ? read back in + check the resulting cubes ?
            # XX Can't do that till we get hybrid-height *loading* implemented.
#            readback_cubes = list(load_cubes(temp_path))

            # Instead, just run a grib-count command + check they saved.
            import subprocess
            command = 'grib_count {}'.format(temp_path)
            grib_count_output_lines = subprocess.check_output(
                command, shell=True)

        # Check we at least saved 4 fields of "something" without errors.
        self.assertEqual(grib_count_output_lines.split(), ['4'])

#        print( readback_cubes )


if __name__ == '__main__':
    tests.main()
