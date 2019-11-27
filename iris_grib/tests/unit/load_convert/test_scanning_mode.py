# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.scanning_mode.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.exceptions import TranslationError

from iris_grib._load_convert import scanning_mode, ScanningMode


class Test(tests.IrisGribTest):
    def test_unset(self):
        expected = ScanningMode(False, False, False, False)
        self.assertEqual(scanning_mode(0x0), expected)

    def test_i_negative(self):
        expected = ScanningMode(i_negative=True, j_positive=False,
                                j_consecutive=False, i_alternative=False)
        self.assertEqual(scanning_mode(0x80), expected)

    def test_j_positive(self):
        expected = ScanningMode(i_negative=False, j_positive=True,
                                j_consecutive=False, i_alternative=False)
        self.assertEqual(scanning_mode(0x40), expected)

    def test_j_consecutive(self):
        expected = ScanningMode(i_negative=False, j_positive=False,
                                j_consecutive=True, i_alternative=False)
        self.assertEqual(scanning_mode(0x20), expected)

    def test_i_alternative(self):
        with self.assertRaises(TranslationError):
            scanning_mode(0x10)


if __name__ == '__main__':
    tests.main()
