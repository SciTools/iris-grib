# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for the `iris_grib.message._RawGribMessage` class.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import gribapi

from iris_grib.message import _RawGribMessage


@tests.skip_data
class Test(tests.IrisGribTest):
    def setUp(self):
        filename = tests.get_data_path(('GRIB', 'uk_t', 'uk_t.grib2'))
        with open(filename, 'rb') as grib_fh:
            grib_id = gribapi.grib_new_from_file(grib_fh)
            self.message = _RawGribMessage(grib_id)

    def test_sections__set(self):
        # Test that sections writes into the _sections attribute.
        _ = self.message.sections
        self.assertNotEqual(self.message._sections, None)

    def test_sections__indexing(self):
        res = self.message.sections[3]['scanningMode']
        expected = 64
        self.assertEqual(expected, res)

    def test__get_message_sections__section_numbers(self):
        res = list(self.message.sections.keys())
        self.assertEqual(res, list(range(9)))

    def test_sections__numberOfSection_value(self):
        # The key `numberOfSection` is repeated in every section meaning that
        # if requested using gribapi it always defaults to its last value (7).
        # This tests that the `_RawGribMessage._get_message_sections`
        # override is functioning.
        section_number = 4
        res = self.message.sections[section_number]['numberOfSection']
        self.assertEqual(res, section_number)


if __name__ == '__main__':
    tests.main()
