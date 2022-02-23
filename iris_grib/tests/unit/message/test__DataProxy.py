# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for the `iris.message._DataProxy` class.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from numpy.random import randint

from iris.exceptions import TranslationError

from iris_grib.message import _DataProxy


class Test__bitmap(tests.IrisGribTest):
    def test_no_bitmap(self):
        section_6 = {'bitMapIndicator': 255, 'bitmap': None}
        data_proxy = _DataProxy(0, 0, 0)
        result = data_proxy._bitmap(section_6)
        self.assertIsNone(result)

    def test_bitmap_present(self):
        bitmap = randint(2, size=(12))
        section_6 = {'bitMapIndicator': 0, 'bitmap': bitmap}
        data_proxy = _DataProxy(0, 0, 0)
        result = data_proxy._bitmap(section_6)
        self.assertArrayEqual(bitmap, result)

    def test_bitmap__invalid_indicator(self):
        section_6 = {'bitMapIndicator': 100, 'bitmap': None}
        data_proxy = _DataProxy(0, 0, 0)
        with self.assertRaisesRegex(TranslationError, 'unsupported bitmap'):
            data_proxy._bitmap(section_6)


if __name__ == '__main__':
    tests.main()
