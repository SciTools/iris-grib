# (C) British Crown Copyright 2014 - 2019, Met Office
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
Unit tests for `iris_grib._load_convert._calculate_increment`.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris_grib._load_convert import _calculate_increment


class Test(tests.IrisGribTest):
    def test_negative(self):
        result = _calculate_increment(-15, -5, 10)
        self.assertEqual(result, 1)

    def test_positive(self):
        result = _calculate_increment(-5, 5, 10)
        self.assertEqual(result, 1)


if __name__ == '__main__':
    tests.main()
