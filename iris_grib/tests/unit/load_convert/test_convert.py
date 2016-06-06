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
"""Test function :func:`iris_grib._load_convert.convert`."""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.exceptions import TranslationError

from iris_grib._load_convert import convert
from iris_grib.tests import mock
from iris_grib.tests.unit import _make_test_message


class Test(tests.IrisGribTest):
    def test_call(self):
        sections = [{'editionNumber': 2}]
        field = _make_test_message(sections)
        this = 'iris_grib._load_convert.grib2_convert'
        factory = mock.sentinel.factory
        func = lambda field, metadata: metadata['factories'].append(factory)
        with mock.patch(this, side_effect=func) as grib2_convert:
            # The call being tested.
            result = convert(field)
            self.assertTrue(grib2_convert.called)
            metadata = ([factory], [], None, None, None, {}, [], [], [])
            self.assertEqual(result, metadata)

    def test_edition_1(self):
        sections = [{'editionNumber': 1}]
        field = _make_test_message(sections)
        with self.assertRaisesRegexp(TranslationError,
                                     'edition 1 is not supported'):
            convert(field)


if __name__ == '__main__':
    tests.main()
