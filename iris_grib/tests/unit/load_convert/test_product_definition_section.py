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

import mock
from iris.coords import DimCoord
from iris_grib._load_convert import product_definition_section

from iris_grib.tests.unit.load_convert import empty_metadata
from iris_grib.tests.unit.load_convert.test_product_definition_template_0 \
    import section_4 as template_0
from iris_grib.tests.unit.load_convert.test_product_definition_template_31 \
    import section_4 as template_31


class Test(tests.IrisGribTest):
    def setUp(self):
        self.patch('warnings.warn')
        self.translate_phenomenon_patch = self.patch(
            'iris_grib._load_convert.translate_phenomenon'
        )


# Tests focussing on the handling of fixed surface elements in section 4.
# Expects/ignores depending on the template number.
class TestFixedSurfaces(Test):
    def generic_fixed_surface_test(self, fs_is_expected, fs_is_present):
        # Whether or not fixed surface elements are expected/present in the
        # section 4 keys, most of the code is shared so we are using a single
        # function with parameters.

        # Prep placeholder variables for product_definition_section.
        discipline = mock.sentinel.discipline
        tablesVersion = mock.sentinel.tablesVersion
        rt_coord = DimCoord(24, 'forecast_reference_time',
                                        units='hours since epoch')
        metadata = empty_metadata()

        # Use the section 4 from either product_definition_section #1 or #31.
        # #1 contains fixed surface elements, #31 does not
        templates = {0: template_0(), 31: template_31()}
        template_number = 0 if fs_is_expected else 31
        section_4 = templates[template_number]
        section_4.update({
            'productDefinitionTemplateNumber': template_number,
            'parameterCategory': None,
            'parameterNumber': None
        })

        fixed_surface_keys = [
            'typeOfFirstFixedSurface',
            'scaledValueOfFirstFixedSurface',
            'typeOfSecondFixedSurface'
        ]
        for key in fixed_surface_keys:
            # Force the presence or absence of the fixed surface elements even
            # when they're respectively ignored or expected.
            if fs_is_present and key not in section_4:
                section_4[key] = template_0()[key]
            elif (not fs_is_present) and key in section_4:
                del section_4[key]

        def run_function():
            # For re-use in every type of test below.
            product_definition_section(
                section_4, metadata, discipline, tablesVersion, rt_coord)

        if fs_is_expected and not fs_is_present:
            # Should error since the expected keys are missing.
            with self.assertRaises(KeyError) as context:
                run_function()
            self.assertTrue('FixedSurface' in str(context.exception))
        else:
            # Should have a successful run for all other circumstances.
            run_function()
            # Translate_phenomenon_patch is the end of the function,
            # and should be able to accept None for the fixed surface
            # arguments. So should always have run.
            self.assertEqual(self.translate_phenomenon_patch.call_count, 1)
            phenom_call_args = self.translate_phenomenon_patch.call_args[1]
            for key in fixed_surface_keys:
                # Check whether None or actual values have been passed for
                # the fixed surface arguments.
                if fs_is_expected:
                    self.assertEqual(phenom_call_args[key], section_4[key])
                else:
                    self.assertEqual(phenom_call_args[key], None)

    def test_fixed_surface_expected_present(self):
        # Standard behaviour for most templates.
        self.generic_fixed_surface_test(fs_is_expected=True,
                                        fs_is_present=True)

    def test_fixed_surface_ignored_absent(self):
        # Standard behaviour for a few templates e.g. #31.
        self.generic_fixed_surface_test(fs_is_expected=False,
                                        fs_is_present=False)

    def test_fixed_surface_expected_absent(self):
        # Unplanned combination, should result in an error.
        self.generic_fixed_surface_test(fs_is_expected=True,
                                        fs_is_present=False)

    def test_fixed_surface_ignored_present(self):
        # Unplanned combination, should be handled same as 'ignored_absent'.
        self.generic_fixed_surface_test(fs_is_expected=False,
                                        fs_is_present=True)


if __name__ == '__main__':
    tests.main()
