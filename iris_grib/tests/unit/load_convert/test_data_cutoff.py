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
Tests for function :func:`iris_grib._load_convert.data_cutoff`.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris_grib._load_convert import _MDI as MDI
from iris_grib._load_convert import data_cutoff
from iris_grib.tests import mock


class TestDataCutoff(tests.IrisGribTest):
    def _check(self, hours, minutes, request_warning, expect_warning=False):
        # Setup the environment.
        patch_target = 'iris_grib._load_convert.options'
        with mock.patch(patch_target) as options:
            options.warn_on_unsupported = request_warning
            with mock.patch('warnings.warn') as warn:
                # The call being tested.
                data_cutoff(hours, minutes)
        # Check the result.
        if expect_warning:
            self.assertEqual(len(warn.mock_calls), 1)
            args, kwargs = warn.call_args
            self.assertIn('data cutoff', args[0])
        else:
            self.assertEqual(len(warn.mock_calls), 0)

    def test_neither(self):
        self._check(MDI, MDI, False)

    def test_hours(self):
        self._check(3, MDI, False)

    def test_minutes(self):
        self._check(MDI, 20, False)

    def test_hours_and_minutes(self):
        self._check(30, 40, False)

    def test_neither_warning(self):
        self._check(MDI, MDI, True, False)

    def test_hours_warning(self):
        self._check(3, MDI, True, True)

    def test_minutes_warning(self):
        self._check(MDI, 20, True, True)

    def test_hours_and_minutes_warning(self):
        self._check(30, 40, True, True)


if __name__ == '__main__':
    tests.main()
