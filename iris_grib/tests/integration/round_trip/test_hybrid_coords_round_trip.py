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
    def setUp(self):
        self.filepath = self.get_testdata_path(
            'faked_sample_hh_grib_data.grib2')
        self.out_path = self.get_result_path(
            '../results/integration/round_trips')
        self.out_name = '/hybrid_height_cube.grib2'
        self.outfile = self.out_path + self.out_name

    def test_hybrid_height(self):
        # Load air temperature cube.
        cube, ref_cube = load_cubes(self.filepath,
                                    ('air_temperature', 'surface_altitude'))
        # Save cubes separately
        save([cube, ref_cube], self.outfile)
        saved_cube = load_cube(self.outfile, 'air_temperature')
        self.assertTrue(saved_cube == cube)


class TestHybridPressureRoundTrip(tests.IrisGribTest):
    def setUp(self):
        self.filepath = self.get_testdata_path(
            'faked_sample_hp_grib_data.grib2')
        self.out_path = self.get_result_path(
            '../results/integration/round_trips')
        self.out_name = '/hybrid_pressure_cube.grib2'
        self.outfile = self.out_path + self.out_name

    def test_hybrid_pressure(self):
        # Load air temperature cube and surface air pressure reference cube
        cube, ref_cube = load_cubes(self.filepath,
                                    ('air_temperature', 'air_pressure'))
        # Save cubes separately
        save([cube, ref_cube], self.outfile)
        saved_cube = load_cube(self.outfile, 'air_temperature')

        # Currently all attributes are lost when saving to grib, so we must
        # equalise them in order to successfully compare all other aspects.
        equalise_attributes([saved_cube, cube])

        self.assertTrue(saved_cube == cube)




