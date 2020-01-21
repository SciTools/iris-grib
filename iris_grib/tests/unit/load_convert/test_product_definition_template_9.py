# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for function
:func:`iris_grib._load_convert.product_definition_template_9`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris.exceptions import TranslationError

from iris_grib._load_convert import product_definition_template_9
from iris_grib._load_convert import Probability, _MDI


class Test(tests.IrisGribTest):
    def setUp(self):
        # Create patches for called routines
        module = 'iris_grib._load_convert'
        self.patch_pdt8_call = self.patch(
            module + '.product_definition_template_8')
        # Construct dummy call arguments
        self.section = {}
        self.section['probabilityType'] = 1
        self.section['scaledValueOfUpperLimit'] = 53
        self.section['scaleFactorOfUpperLimit'] = 1
        self.frt_coord = mock.sentinel.frt_coord
        self.metadata = {'cell_methods': [mock.sentinel.cell_method],
                         'aux_coords_and_dims': []}

    def test_basic(self):
        result = product_definition_template_9(
            self.section, self.metadata, self.frt_coord)
        # Check expected function was called.
        self.assertEqual(
            self.patch_pdt8_call.call_args_list,
            [mock.call(self.section, self.metadata, self.frt_coord)])
        # Check metadata content (N.B. cell_method has been removed!).
        self.assertEqual(self.metadata, {'cell_methods': [],
                                         'aux_coords_and_dims': []})
        # Check result.
        self.assertEqual(result, Probability('above_threshold', 5.3))

    def test_fail_bad_probability_type(self):
        self.section['probabilityType'] = 17
        with self.assertRaisesRegex(TranslationError,
                                    'unsupported probability type'):
            product_definition_template_9(
                self.section, self.metadata, self.frt_coord)

    def test_fail_bad_threshold_value(self):
        self.section['scaledValueOfUpperLimit'] = _MDI
        with self.assertRaisesRegex(TranslationError,
                                    'missing scaled value'):
            product_definition_template_9(
                self.section, self.metadata, self.frt_coord)

    def test_fail_bad_threshold_scalefactor(self):
        self.section['scaleFactorOfUpperLimit'] = _MDI
        with self.assertRaisesRegex(TranslationError,
                                    'missing scale factor'):
            product_definition_template_9(
                self.section, self.metadata, self.frt_coord)


if __name__ == '__main__':
    tests.main()
