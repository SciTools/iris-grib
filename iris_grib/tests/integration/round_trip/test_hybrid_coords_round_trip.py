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
Integration test for loading and saving hybrid height and hybrid pressure data.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests


from iris import load_cube, save
from iris.coords import DimCoord


class TestHybridHeightRoundTrip(tests.IrisGribTest):
    def setUp(self):
        self.filepath = self.get_testdata_path(
            'faked_sample_hh_grib_data.grib2')
        self.out_path = self.get_result_path(
            '../results/integration/round_trips')
        self.out_name = '/hybrid_height_cube.grib2'
        self.outfile = self.out_path + self.out_name

    def test_hybrid_height_load(self):
        # Load air temperature cube and ensure that 'model_level_number' is a
        # dim coord and that 'altitude' is a derived coord.
        cube = load_cube(self.filepath, 'air_temperature')
        self.assertIsInstance(cube.coord('model_level_number'),
                              DimCoord)
        self.assertTrue(cube.derived_coords[0].name() == 'altitude')
        save(cube, self.outfile)

    def test_hybrid_height_save(self):
        # Save air temperature cube as a grib2 file, then reload it and
        # repeat coord checks.
        saved_cube = load_cube(self.outfile)
        self.assertTrue(isinstance(saved_cube.coord('model_level_number'),
                                                    DimCoord))
        self.assertTrue(saved_cube.derived_coords[0].name() == 'altitude')









