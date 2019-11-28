# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.other_time_coord.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import iris.coords

from iris_grib._load_convert import other_time_coord


class TestValid(tests.IrisGribTest):
    def test_t(self):
        rt = iris.coords.DimCoord(48, 'time', units='hours since epoch')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        result = other_time_coord(rt, fp)
        expected = iris.coords.DimCoord(42, 'forecast_reference_time',
                                        units='hours since epoch')
        self.assertEqual(result, expected)

    def test_frt(self):
        rt = iris.coords.DimCoord(48, 'forecast_reference_time',
                                  units='hours since epoch')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        result = other_time_coord(rt, fp)
        expected = iris.coords.DimCoord(54, 'time', units='hours since epoch')
        self.assertEqual(result, expected)


class TestInvalid(tests.IrisGribTest):
    def test_t_with_bounds(self):
        rt = iris.coords.DimCoord(48, 'time', units='hours since epoch',
                                  bounds=[36, 60])
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        with self.assertRaisesRegex(ValueError, 'bounds'):
            other_time_coord(rt, fp)

    def test_frt_with_bounds(self):
        rt = iris.coords.DimCoord(48, 'forecast_reference_time',
                                  units='hours since epoch',
                                  bounds=[42, 54])
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        with self.assertRaisesRegex(ValueError, 'bounds'):
            other_time_coord(rt, fp)

    def test_fp_with_bounds(self):
        rt = iris.coords.DimCoord(48, 'time', units='hours since epoch')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours',
                                  bounds=[3, 9])
        with self.assertRaisesRegex(ValueError, 'bounds'):
            other_time_coord(rt, fp)

    def test_vector_t(self):
        rt = iris.coords.DimCoord([0, 3], 'time', units='hours since epoch')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        with self.assertRaisesRegex(ValueError, 'Vector'):
            other_time_coord(rt, fp)

    def test_vector_frt(self):
        rt = iris.coords.DimCoord([0, 3], 'forecast_reference_time',
                                  units='hours since epoch')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        with self.assertRaisesRegex(ValueError, 'Vector'):
            other_time_coord(rt, fp)

    def test_vector_fp(self):
        rt = iris.coords.DimCoord(48, 'time', units='hours since epoch')
        fp = iris.coords.DimCoord([6, 12], 'forecast_period', units='hours')
        with self.assertRaisesRegex(ValueError, 'Vector'):
            other_time_coord(rt, fp)

    def test_invalid_rt_name(self):
        rt = iris.coords.DimCoord(1, 'height')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        with self.assertRaisesRegex(ValueError, 'reference time'):
            other_time_coord(rt, fp)

    def test_invalid_t_unit(self):
        rt = iris.coords.DimCoord(1, 'time', units='Pa')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        with self.assertRaisesRegex(ValueError, 'unit.*Pa'):
            other_time_coord(rt, fp)

    def test_invalid_frt_unit(self):
        rt = iris.coords.DimCoord(1, 'forecast_reference_time', units='km')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='hours')
        with self.assertRaisesRegex(ValueError, 'unit.*km'):
            other_time_coord(rt, fp)

    def test_invalid_fp_unit(self):
        rt = iris.coords.DimCoord(48, 'forecast_reference_time',
                                  units='hours since epoch')
        fp = iris.coords.DimCoord(6, 'forecast_period', units='kg')
        with self.assertRaisesRegex(ValueError, 'unit.*kg'):
            other_time_coord(rt, fp)


if __name__ == '__main__':
    tests.main()
