# (C) British Crown Copyright 2014 - 2016, Met Office
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
Test function :func:`iris_grib._load_convert.bitmap_section.`

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.exceptions import TranslationError

from iris_grib._load_convert import bitmap_section
from iris_grib.tests.unit import _make_test_message


class Test(tests.IrisGribTest):
    def test_bitmap_unsupported(self):
        # bitMapIndicator in range 1-254.
        # Note that bitMapIndicator = 1-253 and bitMapIndicator = 254 mean two
        # different things, but load_convert treats them identically.
        message = _make_test_message({6: {'bitMapIndicator': 100,
                                          'bitmap': None}})
        with self.assertRaisesRegexp(TranslationError, 'unsupported bitmap'):
            bitmap_section(message.sections[6])


if __name__ == '__main__':
    tests.main()
