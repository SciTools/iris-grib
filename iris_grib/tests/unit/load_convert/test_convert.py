# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Test function :func:`iris_grib._load_convert.convert`."""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris.exceptions import TranslationError

from iris_grib._load_convert import convert
from iris_grib.tests.unit import _make_test_message


class TestGribMessage(tests.IrisGribTest):
    def test_edition_2(self):
        def func(field, metadata):
            return metadata['factories'].append(factory)

        sections = [{'editionNumber': 2}]
        field = _make_test_message(sections)
        this = 'iris_grib._load_convert.grib2_convert'
        factory = mock.sentinel.factory
        with mock.patch(this, side_effect=func) as grib2_convert:
            # The call being tested.
            result = convert(field)
            self.assertTrue(grib2_convert.called)
            metadata = ([factory], [], None, None, None, {}, [], [], [])
            self.assertEqual(result, metadata)

    def test_edition_1_bad(self):
        sections = [{'editionNumber': 1}]
        field = _make_test_message(sections)
        emsg = 'edition 1 is not supported'
        with self.assertRaisesRegex(TranslationError, emsg):
            convert(field)


class TestGribWrapper(tests.IrisGribTest):
    def test_edition_2_bad(self):
        # Test object with no '.sections', and '.edition' ==2.
        field = mock.Mock(edition=2, spec=('edition'))
        emsg = 'edition 2 is not supported'
        with self.assertRaisesRegex(TranslationError, emsg):
            convert(field)

    def test_edition_1(self):
        # Test object with no '.sections', and '.edition' ==1.
        field = mock.Mock(edition=1, spec=('edition'))
        func = 'iris_grib._load_convert.grib1_convert'
        metadata = mock.sentinel.metadata
        with mock.patch(func, return_value=metadata) as grib1_convert:
            result = convert(field)
            grib1_convert.assert_called_once_with(field)
            self.assertEqual(result, metadata)


if __name__ == '__main__':
    tests.main()
