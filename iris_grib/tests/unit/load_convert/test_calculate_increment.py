# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for `iris_grib._load_convert._calculate_increment`.

"""

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

    def test_with_mod(self):
        result = _calculate_increment(355, 5, 10, 360)
        self.assertEqual(result, 1)


if __name__ == '__main__':
    tests.main()
