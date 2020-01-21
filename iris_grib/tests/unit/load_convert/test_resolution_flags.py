# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.resolution_flags.`

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris_grib._load_convert import resolution_flags, ResolutionFlags


class Test(tests.IrisGribTest):
    def test_unset(self):
        expected = ResolutionFlags(False, False, False)
        self.assertEqual(resolution_flags(0x0), expected)

    def test_i_increments_given(self):
        expected = ResolutionFlags(True, False, False)
        self.assertEqual(resolution_flags(0x20), expected)

    def test_j_increments_given(self):
        expected = ResolutionFlags(False, True, False)
        self.assertEqual(resolution_flags(0x10), expected)

    def test_uv_resolved(self):
        expected = ResolutionFlags(False, False, True)
        self.assertEqual(resolution_flags(0x08), expected)


if __name__ == '__main__':
    tests.main()
