# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for `iris_grib._save_rules.fixup_int32_as_uint32`.

"""

# Import iris.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from iris_grib._save_rules import fixup_int32_as_uint32


class Test(tests.IrisGribTest):
    def test_very_negative(self):
        with self.assertRaises(ValueError):
            fixup_int32_as_uint32(-0x80000000)

    def test_negative(self):
        result = fixup_int32_as_uint32(-3)
        self.assertEqual(result, 0x80000003)

    def test_zero(self):
        result = fixup_int32_as_uint32(0)
        self.assertEqual(result, 0)

    def test_positive(self):
        result = fixup_int32_as_uint32(5)
        self.assertEqual(result, 5)

    def test_very_positive(self):
        with self.assertRaises(ValueError):
            fixup_int32_as_uint32(0x80000000)


if __name__ == '__main__':
    tests.main()
