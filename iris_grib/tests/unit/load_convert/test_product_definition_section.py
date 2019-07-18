# (C) British Crown Copyright 2014 - 2019, Met Office
#
# This file is part of iris-grib.
#
# iris-grib is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-grib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-grib.  If not, see <http://www.gnu.org/licenses/>.
"""
Tests for `iris_grib._load_convert.product_definition_section`.

"""

from __future__ import (absolute_import, division, print_function)

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.coords import DimCoord
import mock
import six

from itertools import product

from iris_grib._load_convert import product_definition_section
from iris_grib.tests.unit.load_convert import empty_metadata
from iris_grib.tests.unit.load_convert.test_product_definition_template_0 \
    import section_4 as pdt_0_section_4
from iris_grib.tests.unit.load_convert.test_product_definition_template_31 \
    import section_4 as pdt_31_section_4


class TestFixedSurfaces(tests.IrisGribTest):
    """
    Tests focussing on the handling of fixed surface elements in section 4.
    Expects/ignores depending on the template number.
    """
    def setUp(self):
        self.patch('warnings.warn')
        self.translate_phenomenon_patch = self.patch(
            'iris_grib._load_convert.translate_phenomenon'
        )

        # Prep placeholder variables for product_definition_section.
        self.discipline = mock.sentinel.discipline
        self.tablesVersion = mock.sentinel.tablesVersion
        self.rt_coord = DimCoord(24, 'forecast_reference_time',
                                 units='hours since epoch')
        self.metadata = empty_metadata()

        self.templates = {0: pdt_0_section_4(), 31: pdt_31_section_4()}
        self.fixed_surface_keys = [
            'typeOfFirstFixedSurface',
            'scaledValueOfFirstFixedSurface',
            'typeOfSecondFixedSurface'
        ]

    def _check_fixed_surface(self, fs_is_expected, fs_is_present):
        """
        Whether or not fixed surface elements are expected/present in the
        section 4 keys, most of the code is shared so we are using a single
        function with parameters.
        """

        string_expected = 'Expected' if fs_is_expected else 'Unexpected'
        string_present = 'Present' if fs_is_present else 'Absent'
        print('Fixed Surface Keys *{}* and *{}*... '.format(string_expected,
                                                            string_present))

        # Use the section 4 from either product_definition_section #1 or #31.
        # #0 contains fixed surface elements, #31 does not.
        template_number = 0 if fs_is_expected else 31
        section_4 = self.templates[template_number]
        section_4.update({
            'productDefinitionTemplateNumber': template_number,
            'parameterCategory': None,
            'parameterNumber': None
        })

        for key in self.fixed_surface_keys:
            # Force the presence or absence of the fixed surface elements even
            # when they're respectively ignored or expected.
            if fs_is_present and key not in section_4:
                section_4[key] = pdt_0_section_4()[key]
            elif (not fs_is_present) and key in section_4:
                del section_4[key]

        def run_function():
            # For re-use in every type of test below.
            product_definition_section(
                section_4, self.metadata, self.discipline, self.tablesVersion,
                self.rt_coord)

        if fs_is_expected and not fs_is_present:
            # Should error since the expected keys are missing.
            error_message = 'FixedSurface'
            with six.assertRaisesRegex(self, KeyError, error_message):
                run_function()
        else:
            # Should have a successful run for all other circumstances.

            # Translate_phenomenon_patch is the end of the function,
            # and should be able to accept None for the fixed surface
            # arguments. So should always have run.
            previous_call_count = self.translate_phenomenon_patch.call_count
            run_function()
            self.assertEqual(self.translate_phenomenon_patch.call_count,
                             previous_call_count + 1)
            phenom_call_args = self.translate_phenomenon_patch.call_args[1]
            for key in self.fixed_surface_keys:
                # Check whether None or actual values have been passed for
                # the fixed surface arguments.
                if fs_is_expected:
                    self.assertEqual(phenom_call_args[key], section_4[key])
                else:
                    self.assertIsNone(phenom_call_args[key])

        print('passed')

    def test_all_combinations(self):
        """
        Test all combinations of fixed surface being expected/present

        a. Expected and Present - standard behaviour for most templates
        b. Expected and Absent - unplanned combination, should error
        c. Unexpected and Present - unplanned combination, should be handled
            identically to (d)
        d. Unexpected and Absent - standard behaviour for a few templates
            e.g. #31
        """
        for pair in product([True, False], repeat=2):
            self._check_fixed_surface(*pair)


if __name__ == '__main__':
    tests.main()
