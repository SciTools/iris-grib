# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for the `iris_grib.message.GribMessage` class.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from abc import ABCMeta, abstractmethod
from unittest import mock

import numpy as np
import numpy.ma as ma

from iris._lazy_data import as_concrete_data, is_lazy_data
from iris.exceptions import TranslationError

from iris_grib.message import GribMessage
from iris_grib.tests.unit import _make_test_message


SECTION_6_NO_BITMAP = {'bitMapIndicator': 255, 'bitmap': None}


@tests.skip_data
class Test_messages_from_filename(tests.IrisGribTest):
    def test(self):
        filename = tests.get_data_path(('GRIB', '3_layer_viz',
                                        '3_layer.grib2'))
        messages = list(GribMessage.messages_from_filename(filename))
        self.assertEqual(len(messages), 3)

    def test_release_file(self):
        filename = tests.get_data_path(('GRIB', '3_layer_viz',
                                        '3_layer.grib2'))
        my_file = open(filename)

        import builtins  # noqa: F401
        self.patch('builtins.open', mock.Mock(return_value=my_file))

        messages = list(GribMessage.messages_from_filename(filename))
        self.assertFalse(my_file.closed)
        del messages
        self.assertTrue(my_file.closed)


class Test_sections(tests.IrisGribTest):
    def test(self):
        # Check that the `sections` attribute defers to the `sections`
        # attribute on the underlying _RawGribMessage.
        message = _make_test_message(mock.sentinel.SECTIONS)
        self.assertIs(message.sections, mock.sentinel.SECTIONS)


class Test_data__masked(tests.IrisGribTest):
    def setUp(self):
        self.bitmap = np.array([0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1])
        self.shape = (3, 4)
        self._section_3 = {'sourceOfGridDefinition': 0,
                           'numberOfOctectsForNumberOfPoints': 0,
                           'interpretationOfNumberOfPoints': 0,
                           'gridDefinitionTemplateNumber': 0,
                           'scanningMode': 0,
                           'Nj': self.shape[0],
                           'Ni': self.shape[1]}

    def test_no_bitmap(self):
        values = np.arange(12)
        message = _make_test_message({3: self._section_3,
                                      6: SECTION_6_NO_BITMAP,
                                      7: {'codedValues': values}})
        result = as_concrete_data(message.data)
        expected = values.reshape(self.shape)
        self.assertEqual(result.shape, self.shape)
        self.assertArrayEqual(result, expected)

    def test_bitmap_present(self):
        # Test the behaviour where bitmap and codedValues shapes
        # are not equal.
        input_values = np.arange(5)
        output_values = np.array([-1, -1, 0, 1, -1, -1, -1, 2, -1, 3, -1, 4])
        message = _make_test_message({3: self._section_3,
                                      6: {'bitMapIndicator': 0,
                                          'bitmap': self.bitmap},
                                      7: {'codedValues': input_values}})
        result = as_concrete_data(message.data)
        expected = ma.masked_array(output_values,
                                   np.logical_not(self.bitmap))
        expected = expected.reshape(self.shape)
        self.assertMaskedArrayEqual(result, expected)

    def test_bitmap__shapes_mismatch(self):
        # Test the behaviour where bitmap and codedValues shapes do not match.
        # Too many or too few unmasked values in codedValues will cause this.
        values = np.arange(6)
        message = _make_test_message({3: self._section_3,
                                      6: {'bitMapIndicator': 0,
                                          'bitmap': self.bitmap},
                                      7: {'codedValues': values}})
        with self.assertRaisesRegex(TranslationError, 'do not match'):
            as_concrete_data(message.data)

    def test_bitmap__invalid_indicator(self):
        values = np.arange(12)
        message = _make_test_message({3: self._section_3,
                                      6: {'bitMapIndicator': 100,
                                          'bitmap': None},
                                      7: {'codedValues': values}})
        with self.assertRaisesRegex(TranslationError, 'unsupported bitmap'):
            as_concrete_data(message.data)


class Test_data__unsupported(tests.IrisGribTest):
    def test_unsupported_grid_definition(self):
        message = _make_test_message({3: {'sourceOfGridDefinition': 1},
                                      6: SECTION_6_NO_BITMAP})
        with self.assertRaisesRegex(TranslationError, 'source'):
            message.data

    def test_unsupported_quasi_regular__number_of_octets(self):
        message = _make_test_message(
            {3: {'sourceOfGridDefinition': 0,
                 'numberOfOctectsForNumberOfPoints': 1,
                 'gridDefinitionTemplateNumber': 0},
             6: SECTION_6_NO_BITMAP})
        with self.assertRaisesRegex(TranslationError, 'quasi-regular'):
            message.data

    def test_unsupported_quasi_regular__interpretation(self):
        message = _make_test_message(
            {3: {'sourceOfGridDefinition': 0,
                 'numberOfOctectsForNumberOfPoints': 0,
                 'interpretationOfNumberOfPoints': 1,
                 'gridDefinitionTemplateNumber': 0},
             6: SECTION_6_NO_BITMAP})
        with self.assertRaisesRegex(TranslationError, 'quasi-regular'):
            message.data

    def test_unsupported_template(self):
        message = _make_test_message(
            {3: {'sourceOfGridDefinition': 0,
                 'numberOfOctectsForNumberOfPoints': 0,
                 'interpretationOfNumberOfPoints': 0,
                 'gridDefinitionTemplateNumber': 2}})
        with self.assertRaisesRegex(TranslationError, 'template'):
            message.data


# Abstract, mix-in class for testing the `data` attribute for various
# grid definition templates.
class Mixin_data__grid_template(metaclass=ABCMeta):
    @abstractmethod
    def section_3(self, scanning_mode):
        raise NotImplementedError()

    def test_unsupported_scanning_mode(self):
        message = _make_test_message(
            {3: self.section_3(1),
             6: SECTION_6_NO_BITMAP})
        with self.assertRaisesRegex(TranslationError, 'scanning mode'):
            message.data

    def _test(self, scanning_mode):
        message = _make_test_message(
            {3: self.section_3(scanning_mode),
             6: SECTION_6_NO_BITMAP,
             7: {'codedValues': np.arange(12)}})
        data = message.data
        self.assertTrue(is_lazy_data(data))
        self.assertEqual(data.shape, (3, 4))
        self.assertEqual(data.dtype, np.floating)
        self.assertArrayEqual(as_concrete_data(data),
                              np.arange(12).reshape(3, 4))

    def test_regular_mode_0(self):
        self._test(0)

    def test_regular_mode_64(self):
        self._test(64)

    def test_regular_mode_128(self):
        self._test(128)

    def test_regular_mode_64_128(self):
        self._test(64 | 128)


def _example_section_3(grib_definition_template_number, scanning_mode):
    return {'sourceOfGridDefinition': 0,
            'numberOfOctectsForNumberOfPoints': 0,
            'interpretationOfNumberOfPoints': 0,
            'gridDefinitionTemplateNumber': grib_definition_template_number,
            'scanningMode': scanning_mode,
            'Nj': 3,
            'Ni': 4}


class Test_data__grid_template_0(tests.IrisGribTest,
                                 Mixin_data__grid_template):
    def section_3(self, scanning_mode):
        return _example_section_3(0, scanning_mode)


class Test_data__grid_template_1(tests.IrisGribTest,
                                 Mixin_data__grid_template):
    def section_3(self, scanning_mode):
        return _example_section_3(1, scanning_mode)


class Test_data__grid_template_5(tests.IrisGribTest,
                                 Mixin_data__grid_template):
    def section_3(self, scanning_mode):
        return _example_section_3(5, scanning_mode)


class Test_data__grid_template_12(tests.IrisGribTest,
                                  Mixin_data__grid_template):
    def section_3(self, scanning_mode):
        return _example_section_3(12, scanning_mode)


class Test_data__grid_template_30(tests.IrisGribTest,
                                  Mixin_data__grid_template):
    def section_3(self, scanning_mode):
        section_3 = _example_section_3(30, scanning_mode)
        # Dimensions are 'Nx' + 'Ny' instead of 'Ni' + 'Nj'.
        section_3['Nx'] = section_3['Ni']
        section_3['Ny'] = section_3['Nj']
        del section_3['Ni']
        del section_3['Nj']
        return section_3


class Test_data__grid_template_40_regular(tests.IrisGribTest,
                                          Mixin_data__grid_template):
    def section_3(self, scanning_mode):
        return _example_section_3(40, scanning_mode)


class Test_data__grid_template_90(tests.IrisGribTest,
                                  Mixin_data__grid_template):
    def section_3(self, scanning_mode):
        section_3 = _example_section_3(90, scanning_mode)
        # Exceptionally, dimensions are 'Nx' + 'Ny' instead of 'Ni' + 'Nj'.
        section_3['Nx'] = section_3['Ni']
        section_3['Ny'] = section_3['Nj']
        del section_3['Ni']
        del section_3['Nj']
        return section_3


class Test_data__grid_template_140(tests.IrisGribTest,
                                   Mixin_data__grid_template):
    def section_3(self, scanning_mode):
        section_3 = _example_section_3(140, scanning_mode)
        section_3['numberOfPointsAlongXAxis'] = section_3['Ni']
        section_3['numberOfPointsAlongYAxis'] = section_3['Nj']
        del section_3['Ni']
        del section_3['Nj']
        return section_3


class Test_data__unknown_grid_template(tests.IrisGribTest):
    def test(self):
        message = _make_test_message(
            {3: _example_section_3(999, 0),
             6: SECTION_6_NO_BITMAP,
             7: {'codedValues': np.arange(12)}})
        with self.assertRaisesRegex(TranslationError,
                                    'template 999 is not supported'):
            _ = message.data


if __name__ == '__main__':
    tests.main()
