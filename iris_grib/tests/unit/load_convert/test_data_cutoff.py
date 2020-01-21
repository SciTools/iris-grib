# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for function :func:`iris_grib._load_convert.data_cutoff`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris_grib._load_convert import _MDI as MDI
from iris_grib._load_convert import data_cutoff


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
