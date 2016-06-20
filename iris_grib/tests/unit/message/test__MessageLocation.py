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
Unit tests for the `iris.message._MessageLocation` class.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris_grib.message import _MessageLocation
from iris_grib.tests import mock


class Test(tests.IrisGribTest):
    def test(self):
        message_location = _MessageLocation(mock.sentinel.filename,
                                            mock.sentinel.location)
        patch_target = 'iris_grib.message._RawGribMessage.from_file_offset'
        expected = mock.sentinel.message
        with mock.patch(patch_target, return_value=expected) as rgm:
            result = message_location()
        rgm.assert_called_once_with(mock.sentinel.filename,
                                    mock.sentinel.location)
        self.assertIs(result, expected)


if __name__ == '__main__':
    tests.main()
