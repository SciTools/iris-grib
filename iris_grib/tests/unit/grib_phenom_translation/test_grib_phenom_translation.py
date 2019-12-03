# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
'''
Unit tests for the mod:`iris_grib.grib_phenom_translation` module.

Carried over from old iris/tests/test_grib_phenom_translation.py.
Code is out of step with current test conventions and standards.

'''

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import cf_units

import iris_grib.grib_phenom_translation as gptx
from iris_grib.grib_phenom_translation import GRIBCode


class TestGribLookupTableType(tests.IrisTest):
    def test_lookuptable_type(self):
        ll = gptx._LookupTable([('a', 1), ('b', 2)])
        assert ll['a'] == 1
        assert ll['q'] is None
        ll['q'] = 15
        assert ll['q'] == 15
        ll['q'] = 15
        assert ll['q'] == 15
        with self.assertRaises(KeyError):
            ll['q'] = 7
        del ll['q']
        ll['q'] = 7
        assert ll['q'] == 7


class TestGribPhenomenonLookup(tests.IrisTest):
    def test_grib1_cf_lookup(self):
        def check_grib1_cf(param,
                           standard_name, long_name, units,
                           height=None,
                           t2version=128, centre=98, expect_none=False):
            a_cf_unit = cf_units.Unit(units)
            cfdata = gptx.grib1_phenom_to_cf_info(param_number=param,
                                                  table2_version=t2version,
                                                  centre_number=centre)
            if expect_none:
                self.assertIsNone(cfdata)
            else:
                self.assertEqual(cfdata.standard_name, standard_name)
                self.assertEqual(cfdata.long_name, long_name)
                self.assertEqual(cfdata.units, a_cf_unit)
                if height is None:
                    self.assertIsNone(cfdata.set_height)
                else:
                    self.assertEqual(cfdata.set_height, float(height))

        check_grib1_cf(165, 'x_wind', None, 'm s-1', 10.0)
        check_grib1_cf(168, 'dew_point_temperature', None, 'K', 2)
        check_grib1_cf(130, 'air_temperature', None, 'K')
        check_grib1_cf(235, None, "grib_skin_temperature", "K")
        check_grib1_cf(235, None, "grib_skin_temperature", "K",
                       t2version=9999, expect_none=True)
        check_grib1_cf(235, None, "grib_skin_temperature", "K",
                       centre=9999, expect_none=True)
        check_grib1_cf(9999, None, "grib_skin_temperature", "K",
                       expect_none=True)

    def test_grib2_cf_lookup(self):
        def check_grib2_cf(discipline, category, number,
                           standard_name, long_name, units,
                           expect_none=False):
            a_cf_unit = cf_units.Unit(units)
            cfdata = gptx.grib2_phenom_to_cf_info(param_discipline=discipline,
                                                  param_category=category,
                                                  param_number=number)
            if expect_none:
                self.assertIsNone(cfdata)
            else:
                self.assertEqual(cfdata.standard_name, standard_name)
                self.assertEqual(cfdata.long_name, long_name)
                self.assertEqual(cfdata.units, a_cf_unit)

        # These should work
        check_grib2_cf(0, 0, 2, "air_potential_temperature", None, "K")
        check_grib2_cf(0, 19, 1, None, "grib_physical_atmosphere_albedo", "%")
        check_grib2_cf(2, 0, 2, "soil_temperature", None, "K")
        check_grib2_cf(10, 2, 0, "sea_ice_area_fraction", None, 1)
        check_grib2_cf(2, 0, 0, "land_area_fraction", None, 1)
        check_grib2_cf(0, 19, 1, None, "grib_physical_atmosphere_albedo", "%")
        check_grib2_cf(0, 1, 64,
                       "atmosphere_mass_content_of_water_vapor", None,
                       "kg m-2")
        check_grib2_cf(2, 0, 7, "surface_altitude", None, "m")

        # These should fail
        check_grib2_cf(9999, 2, 0, "sea_ice_area_fraction", None, 1,
                       expect_none=True)
        check_grib2_cf(10, 9999, 0, "sea_ice_area_fraction", None, 1,
                       expect_none=True)
        check_grib2_cf(10, 2, 9999, "sea_ice_area_fraction", None, 1,
                       expect_none=True)

    def test_cf_grib2_lookup(self):
        def check_cf_grib2(standard_name, long_name,
                           discipline, category, number, units,
                           expect_none=False):
            a_cf_unit = cf_units.Unit(units)
            gribdata = gptx.cf_phenom_to_grib2_info(standard_name, long_name)
            if expect_none:
                self.assertIsNone(gribdata)
            else:
                self.assertEqual(gribdata.discipline, discipline)
                self.assertEqual(gribdata.category, category)
                self.assertEqual(gribdata.number, number)
                self.assertEqual(gribdata.units, a_cf_unit)

        # These should work
        check_cf_grib2("sea_surface_temperature", None,
                       10, 3, 0, 'K')
        check_cf_grib2("air_temperature", None,
                       0, 0, 0, 'K')
        check_cf_grib2("soil_temperature", None,
                       2, 0, 2, "K")
        check_cf_grib2("land_area_fraction", None,
                       2, 0, 0, '1')
        check_cf_grib2("land_binary_mask", None,
                       2, 0, 0, '1')
        check_cf_grib2("atmosphere_mass_content_of_water_vapor", None,
                       0, 1, 64, "kg m-2")
        check_cf_grib2("surface_altitude", None,
                       2, 0, 7, "m")

        # These should fail
        check_cf_grib2("air_temperature", "user_long_UNRECOGNISED",
                       0, 0, 0, 'K')
        check_cf_grib2("air_temperature_UNRECOGNISED", None,
                       0, 0, 0, 'K',
                       expect_none=True)
        check_cf_grib2(None, "user_long_UNRECOGNISED",
                       0, 0, 0, 'K',
                       expect_none=True)
        check_cf_grib2(None, "precipitable_water",
                       0, 1, 3, 'kg m-2')
        check_cf_grib2("invalid_unknown", "precipitable_water",
                       0, 1, 3, 'kg m-2',
                       expect_none=True)
        check_cf_grib2(None, None, 0, 0, 0, '',
                       expect_none=True)


class TestGRIBcode(tests.IrisTest):
    # GRIBCode is basically a namedtuple, so not all behaviour needs testing.
    # However, creation is a bit special so exercise all those cases.
    def test_create_from_keys(self):
        gribcode = GRIBCode(
            edition_or_string=5,
            discipline=7,
            category=4,
            number=199)
        self.assertEqual(gribcode.edition, 5)
        self.assertEqual(gribcode.discipline, 7)
        self.assertEqual(gribcode.category, 4)
        self.assertEqual(gribcode.number, 199)

    def test_create_from_args(self):
        gribcode = GRIBCode(7, 3, 12, 99)
        self.assertEqual(gribcode.edition, 7)
        self.assertEqual(gribcode.discipline, 3)
        self.assertEqual(gribcode.category, 12)
        self.assertEqual(gribcode.number, 99)

    def test_create_is_copy(self):
        gribcode1 = GRIBCode(7, 3, 12, 99)
        gribcode2 = GRIBCode(7, 3, 12, 99)
        self.assertEqual(gribcode1, gribcode2)
        self.assertIsNot(gribcode1, gribcode2)

    def test_create_from_gribcode(self):
        gribcode1 = GRIBCode((4, 3, 2, 1))
        gribcode2 = GRIBCode(gribcode1)
        self.assertEqual(gribcode1, gribcode2)
        # NOTE: *not* passthrough : it creates a copy
        # (though maybe not too significant, as it is immutable anyway?)
        self.assertIsNot(gribcode1, gribcode2)

    def test_create_from_string(self):
        gribcode = GRIBCode('xxx12xs-34 -5,678qqqq')
        # NOTE: args 2 and 3 are *not* negative.
        self.assertEqual(gribcode, GRIBCode(12, 34, 5, 678))

    def test_create_from_own_string(self):
        # Check that GRIBCode string reprs are valid as create arguments.
        gribcode = GRIBCode(
            edition_or_string=2,
            discipline=17,
            category=94,
            number=231)
        grib_param_string = str(gribcode)
        newcode = GRIBCode(grib_param_string)
        self.assertEqual(newcode, gribcode)

    def test_create_from_tuple(self):
        gribcode = GRIBCode((4, 3, 2, 1))
        self.assertEqual(gribcode, GRIBCode(4, 3, 2, 1))

    def test_create_bad_nargs(self):
        # Between 1 and 4 args is not invalid call syntax, but it should fail.
        with self.assertRaisesRegex(
                ValueError,
                'Cannot create GRIBCode from 2 arguments'):
            GRIBCode(1, 2)

    def test_create_bad_single_arg_None(self):
        with self.assertRaisesRegex(
                ValueError,
                'Cannot create GRIBCode from 0 arguments'):
            GRIBCode(None)

    def test_create_bad_single_arg_empty_string(self):
        with self.assertRaisesRegex(
                ValueError,
                'Invalid argument for GRIBCode creation'):
            GRIBCode('')

    def test_create_bad_single_arg_nonums(self):
        with self.assertRaisesRegex(
                ValueError,
                'Invalid argument for GRIBCode creation'):
            GRIBCode('saas- dsa- ')

    def test_create_bad_single_arg_less_than_4_nums(self):
        with self.assertRaisesRegex(
                ValueError,
                'Invalid argument for GRIBCode creation'):
            GRIBCode('1,2,3')

    def test_create_bad_single_arg_number(self):
        with self.assertRaisesRegex(
                ValueError,
                'Invalid argument for GRIBCode creation'):
            GRIBCode(4)

    def test_create_bad_single_arg_single_numeric(self):
        with self.assertRaisesRegex(
                ValueError,
                'Invalid argument for GRIBCode creation'):
            GRIBCode('44')

    def test_create_string_more_than_4_nums(self):
        # Note: does not error, just discards the extra.
        gribcode = GRIBCode('1,2,3,4,5,6,7,8')
        self.assertEqual(gribcode, GRIBCode(1, 2, 3, 4))

    def test__str__(self):
        result = str(GRIBCode(2, 17, 3, 123))
        self.assertEqual(result, 'GRIB2:d017c003n123')


if __name__ == '__main__':
    tests.main()
