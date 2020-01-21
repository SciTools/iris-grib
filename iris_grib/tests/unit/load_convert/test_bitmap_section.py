# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.bitmap_section.`

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.exceptions import TranslationError

from iris_grib._load_convert import bitmap_section
from iris_grib.tests.unit import _make_test_message


class Test(tests.IrisGribTest):
    def test_bitmap_unsupported(self):
        # bitMapIndicator in range 1-254.
        # Note that bitMapIndicator = 1-253 and bitMapIndicator = 254 mean two
        # different things, but load_convert treats them identically.
        message = _make_test_message({6: {'bitMapIndicator': 100,
                                          'bitmap': None}})
        with self.assertRaisesRegex(TranslationError, 'unsupported bitmap'):
            bitmap_section(message.sections[6])


if __name__ == '__main__':
    tests.main()
