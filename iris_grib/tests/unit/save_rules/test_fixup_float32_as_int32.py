# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for `iris_grib._save_rules.fixup_float32_as_int32`.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris_grib._save_rules import fixup_float32_as_int32


class Test(tests.IrisGribTest):
    def test_positive_zero(self):
        result = fixup_float32_as_int32(0.0)
        self.assertEqual(result, 0)

    def test_negative_zero(self):
        result = fixup_float32_as_int32(-0.0)
        self.assertEqual(result, 0)

    def test_high_bit_clear_1(self):
        # Start with the float32 value for the bit pattern 0x00000001.
        result = fixup_float32_as_int32(1.401298464324817e-45)
        self.assertEqual(result, 1)

    def test_high_bit_clear_2(self):
        # Start with the float32 value for the bit pattern 0x00000002.
        result = fixup_float32_as_int32(2.802596928649634e-45)
        self.assertEqual(result, 2)

    def test_high_bit_set_1(self):
        # Start with the float32 value for the bit pattern 0x80000001.
        result = fixup_float32_as_int32(-1.401298464324817e-45)
        self.assertEqual(result, -1)

    def test_high_bit_set_2(self):
        # Start with the float32 value for the bit pattern 0x80000002.
        result = fixup_float32_as_int32(-2.802596928649634e-45)
        self.assertEqual(result, -2)


if __name__ == '__main__':
    tests.main()
