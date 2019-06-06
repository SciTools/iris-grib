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
Tests for function :func:`iris_grib._load_convert.product_definition_section`.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from copy import deepcopy
import mock

from cf_units import Unit
from iris.coords import DimCoord

from iris_grib._load_convert import product_definition_section
from iris_grib._load_convert import vertical_coords
from iris_grib.grib_phenom_translation import _GribToCfDataClass

from iris_grib.tests.unit.load_convert import empty_metadata
from iris_grib.tests.unit.load_convert.test_product_definition_template_0 \
    import section_4 as template_0
from iris_grib.tests.unit.load_convert.test_product_definition_template_31 \
    import section_4 as template_31


class Test(tests.IrisGribTest):
    def setUp(self):
        self.patch('warnings.warn')
        # self.product_definition_section_patch = self.patch(
        #     'iris_grib._load_convert.product_definition_section'
        # )
        # self.vertical_coords_patch = self.patch(
        #     'iris_grib._load_convert.vertical_coords'
        # )
        self.translate_phenomenon_patch = self.patch(
            'iris_grib._load_convert.translate_phenomenon'
        )


class TestFixedSurfaces(Test):
    def generic_fixed_surface_test(self, fs_is_expected, fs_is_present):
        discipline = mock.sentinel.discipline
        tablesVersion = mock.sentinel.tablesVersion
        rt_coord = DimCoord(24, 'forecast_reference_time',
                                        units='hours since epoch')
        metadata = empty_metadata()

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
            if fs_is_present and key not in section_4:
                section_4[key] = template_0()[key]
            elif (not fs_is_present) and key in section_4:
                del section_4[key]

        def run_function():
            product_definition_section(
                section_4, metadata, discipline, tablesVersion, rt_coord)

        if fs_is_expected and not fs_is_present:
            with self.assertRaises(KeyError) as context:
                run_function()
            self.assertTrue('FixedSurface' in str(context.exception))
        else:
            run_function()
            self.assertEqual(self.translate_phenomenon_patch.call_count, 1)
            phenom_call_args = self.translate_phenomenon_patch.call_args[1]
            for key in fixed_surface_keys:
                if fs_is_expected:
                    self.assertEqual(phenom_call_args[key], section_4[key])
                else:
                    self.assertEqual(phenom_call_args[key], None)

    def test_fixed_surface_expected_present(self):
        self.generic_fixed_surface_test(fs_is_expected=True,
                                        fs_is_present=True)

    def test_fixed_surface_expected_absent(self):
        self.generic_fixed_surface_test(fs_is_expected=True,
                                        fs_is_present=False)

    def test_fixed_surface_ignored_present(self):
        self.generic_fixed_surface_test(fs_is_expected=False,
                                        fs_is_present=True)

    def test_fixed_surface_ignored_absent(self):
        self.generic_fixed_surface_test(fs_is_expected=False,
                                        fs_is_present=False)
