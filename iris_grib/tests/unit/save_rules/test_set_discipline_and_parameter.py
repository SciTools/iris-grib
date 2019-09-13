# (C) British Crown Copyright 2019, Met Office
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
"""Unit tests for `iris_grib.grib_save_rules.set_discipline_and_parameter`."""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests
import mock

from iris.cube import Cube

from iris_grib.grib_phenom_translation import GribCode

from iris_grib._save_rules import set_discipline_and_parameter


class TestPhenomenonCoding(tests.IrisGribTest):
    def setUp(self):
        # A mock cube with empty phenomenon-specifying metadata.
        self.mock_cube = mock.Mock(
            spec=Cube,
            standard_name=None,
            long_name=None,
            attributes={})

    def _check_coding(self, cube, discipline, paramCategory, paramNumber):
        # Check that encoding 'cube' writes the expected phenomenon keys.
        grib_set_patch = self.patch(
            'iris_grib._save_rules.gribapi.grib_set')
        mock_message = mock.sentinel.grib2_message

        set_discipline_and_parameter(cube, mock_message)

        expected_calls = [
            mock.call(mock_message, "discipline", discipline),
            mock.call(mock_message, "parameterCategory", paramCategory),
            mock.call(mock_message, "parameterNumber", paramNumber)]

        self.assertEqual(grib_set_patch.call_args_list, expected_calls)

    def test_unknown_phenomenon(self):
        cube = self.mock_cube
        self._check_coding(cube, 255, 255, 255)

    def test_known_standard_name(self):
        cube = self.mock_cube
        cube.standard_name = 'sea_water_y_velocity'
        self._check_coding(cube, 10, 1, 3)  # as seen in _grib_cf_map.py

    def test_gribcode_attribute_object(self):
        cube = self.mock_cube
        cube.attributes = {'GRIB_CODING': GribCode(2, 7, 12, 99)}
        self._check_coding(cube, 7, 12, 99)

    def test_gribcode_attribute_string(self):
        cube = self.mock_cube
        self.mock_cube.attributes = {'GRIB_CODING': '2, 9, 33, 177'}
        self._check_coding(cube, 9, 33, 177)

    def test_gribcode_attribute_tuple(self):
        cube = self.mock_cube
        self.mock_cube.attributes = {'GRIB_CODING': (2, 33, 4, 12)}
        self._check_coding(cube, 33, 4, 12)

    def test_gribcode_attribute_not_edition_2(self):
        cube = self.mock_cube
        cube.attributes = {'GRIB_CODING': GribCode(1, 7, 12, 99)}
        self._check_coding(cube, 255, 255, 255)


if __name__ == "__main__":
    tests.main()
