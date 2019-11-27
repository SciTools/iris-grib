# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.time_range_unit.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from cf_units import Unit
from iris.exceptions import TranslationError

from iris_grib._load_convert import time_range_unit


class Test(tests.IrisGribTest):
    def setUp(self):
        self.unit_by_indicator = {0: Unit('minutes'),
                                  1: Unit('hours'),
                                  2: Unit('days'),
                                  10: Unit('3 hours'),
                                  11: Unit('6 hours'),
                                  12: Unit('12 hours'),
                                  13: Unit('seconds')}

    def test_units(self):
        for indicator, unit in self.unit_by_indicator.items():
            result = time_range_unit(indicator)
            self.assertEqual(result, unit)

    def test_bad_indicator(self):
        emsg = 'unsupported time range'
        with self.assertRaisesRegex(TranslationError, emsg):
            time_range_unit(-1)


if __name__ == '__main__':
    tests.main()
