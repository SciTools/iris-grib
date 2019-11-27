# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for `iris_grib._load_convert.fixup_int32_from_uint32`.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris_grib._load_convert import fixup_int32_from_uint32


class Test(tests.IrisGribTest):
    def test_negative(self):
        result = fixup_int32_from_uint32(0x80000005)
        self.assertEqual(result, -5)

    def test_negative_zero(self):
        result = fixup_int32_from_uint32(0x80000000)
        self.assertEqual(result, 0)

    def test_zero(self):
        result = fixup_int32_from_uint32(0)
        self.assertEqual(result, 0)

    def test_positive(self):
        result = fixup_int32_from_uint32(200000)
        self.assertEqual(result, 200000)

    def test_already_negative(self):
        # If we *already* have a negative value the fixup routine should
        # leave it alone.
        result = fixup_int32_from_uint32(-7)
        self.assertEqual(result, -7)


if __name__ == '__main__':
    tests.main()
