# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Tests for function
:func:`iris_grib._load_convert.product_definition_template_5`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris.exceptions import TranslationError
from iris.coords import DimCoord

from iris_grib._load_convert import product_definition_template_5
from iris_grib._load_convert import Probability, _MDI
from .test_product_definition_template_0 import section_4


class Test(tests.IrisGribTest):
    def setUp(self):
        # Create patches for called routines
        module = "iris_grib._load_convert"
        self.patch_pdt0_call = self.patch(module + ".product_definition_template_0")
        # Construct dummy call arguments
        self.section = section_4()
        self.section["probabilityType"] = 1
        self.section["scaledValueOfUpperLimit"] = 53
        self.section["scaleFactorOfUpperLimit"] = 1
        self.frt_coord = DimCoord(
            24, "forecast_reference_time", units="hours since epoch"
        )
        self.metadata = {
            "cell_methods": [],
            "aux_coords_and_dims": [],
        }

    def test_basic(self):
        result = product_definition_template_5(
            self.section, self.metadata, self.frt_coord
        )
        # Check expected functions were called.
        self.assertEqual(
            self.patch_pdt0_call.call_args_list,
            [mock.call(self.section, self.metadata, self.frt_coord)],
        )
        # Check metadata content (N.B. cell_method has been removed!).
        self.assertEqual(self.metadata, {"cell_methods": [], "aux_coords_and_dims": []})
        # Check result.
        self.assertEqual(result, Probability("above_threshold", 5.3))

    def test_below_upper_threshold(self):
        self.section["probabilityType"] = 4
        result = product_definition_template_5(
            self.section, self.metadata, self.frt_coord
        )
        # Check result.
        self.assertEqual(result, Probability("below_threshold", 5.3))

    def test_above_lower_threshold(self):
        self.section["probabilityType"] = 3
        self.section["scaledValueOfUpperLimit"] = None
        self.section["scaleFactorOfUpperLimit"] = None
        self.section["scaledValueOfLowerLimit"] = 53
        self.section["scaleFactorOfLowerLimit"] = 1
        result = product_definition_template_5(
            self.section, self.metadata, self.frt_coord
        )
        # Check result.
        self.assertEqual(result, Probability("above_threshold", 5.3))

    def test_below_lower_threshold(self):
        self.section["probabilityType"] = 0
        self.section["scaledValueOfUpperLimit"] = None
        self.section["scaleFactorOfUpperLimit"] = None
        self.section["scaledValueOfLowerLimit"] = 53
        self.section["scaleFactorOfLowerLimit"] = 1

        result = product_definition_template_5(
            self.section, self.metadata, self.frt_coord
        )
        # Check result.
        self.assertEqual(result, Probability("below_threshold", 5.3))

    def test_fail_bad_probability_type(self):
        self.section["probabilityType"] = 17
        with self.assertRaisesRegex(TranslationError, "unsupported probability type"):
            product_definition_template_5(self.section, self.metadata, self.frt_coord)

    def test_fail_bad_threshold_value(self):
        self.section["scaledValueOfUpperLimit"] = _MDI
        with self.assertRaisesRegex(TranslationError, "missing scaled value"):
            product_definition_template_5(self.section, self.metadata, self.frt_coord)

    def test_fail_bad_threshold_scalefactor(self):
        self.section["scaleFactorOfUpperLimit"] = _MDI
        with self.assertRaisesRegex(TranslationError, "missing scale factor"):
            product_definition_template_5(self.section, self.metadata, self.frt_coord)


if __name__ == "__main__":
    tests.main()
