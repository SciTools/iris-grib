# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for `iris_grib._load_convert.fixup_float32_from_int32`.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris_grib._load_convert import fixup_float32_from_int32


class Test(tests.IrisGribTest):
    def test_negative(self):
        result = fixup_float32_from_int32(-0x3f000000)
        self.assertEqual(result, -0.5)

    def test_zero(self):
        result = fixup_float32_from_int32(0)
        self.assertEqual(result, 0)

    def test_positive(self):
        result = fixup_float32_from_int32(0x3f000000)
        self.assertEqual(result, 0.5)


if __name__ == '__main__':
    tests.main()
