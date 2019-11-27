# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for function :func:`iris_grib._load_convert._hindcast_fix`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from collections import namedtuple

from iris_grib._load_convert import _hindcast_fix as hindcast_fix


class TestHindcastFix(tests.IrisGribTest):
    # setup tests : provided value, fix-applies, expected-fixed
    FixTest = namedtuple('FixTest', ('given', 'fixable', 'fixed'))
    test_values = [
        FixTest(0, False, None),
        FixTest(100, False, None),
        FixTest(2 * 2**30 - 1, False, None),
        FixTest(2 * 2**30, False, None),
        FixTest(2 * 2**30 + 1, True, -1),
        FixTest(2 * 2**30 + 2, True, -2),
        FixTest(3 * 2**30 - 1, True, -(2**30 - 1)),
        FixTest(3 * 2**30, False, None)]

    def setUp(self):
        self.patch_warn = self.patch('warnings.warn')

    def test_fix(self):
        # Check hindcast fixing.
        for given, fixable, fixed in self.test_values:
            result = hindcast_fix(given)
            expected = fixed if fixable else given
            self.assertEqual(result, expected)

    def test_fix_warning(self):
        # Check warning appears when enabled.
        self.patch('iris_grib._load_convert.options.warn_on_unsupported', True)
        hindcast_fix(2 * 2**30 + 5)
        self.assertEqual(self.patch_warn.call_count, 1)
        self.assertIn('Re-interpreting large grib forecastTime',
                      self.patch_warn.call_args[0][0])

    def test_fix_warning_disabled(self):
        # Default is no warning.
        hindcast_fix(2 * 2**30 + 5)
        self.assertEqual(self.patch_warn.call_count, 0)


if __name__ == '__main__':
    tests.main()
