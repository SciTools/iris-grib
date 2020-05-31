# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.data_section`.

"""

# import iris_grib.tests first so that some things can be initialised before
# importing anything else
import iris_grib.tests as tests

from unittest import mock

import gribapi
import iris.cube
import numpy as np

from iris_grib._save_rules import data_section


GRIB_API = 'iris_grib._save_rules.gribapi'
GRIB_MESSAGE = mock.sentinel.GRIB_MESSAGE


class TestMDI(tests.IrisGribTest):
    def assertBitmapOff(self, grib_api):
        # Check the use of a mask has been turned off via:
        #   gribapi.grib_set(grib_message, 'bitmapPresent', 0)
        grib_api.grib_set.assert_called_once_with(GRIB_MESSAGE,
                                                  'bitmapPresent', 0)

    def assertBitmapOn(self, grib_api, fill_value):
        # Check the use of a mask has been turned on via:
        #   gribapi.grib_set(grib_message, 'bitmapPresent', 1)
        #   gribapi.grib_set_double(grib_message, 'missingValue', fill_value)
        grib_api.grib_set.assert_called_once_with(GRIB_MESSAGE,
                                                  'bitmapPresent', 1)
        grib_api.grib_set_double.assert_called_once_with(GRIB_MESSAGE,
                                                         'missingValue',
                                                         fill_value)

    def assertBitmapRange(self, grib_api, min_data, max_data):
        # Check the use of a mask has been turned on via:
        #   gribapi.grib_set(grib_message, 'bitmapPresent', 1)
        #   gribapi.grib_set_double(grib_message, 'missingValue', ...)
        # and that a suitable fill value has been chosen.
        grib_api.grib_set.assert_called_once_with(GRIB_MESSAGE,
                                                  'bitmapPresent', 1)
        args, = grib_api.grib_set_double.call_args_list
        (message, key, fill_value), kwargs = args
        self.assertIs(message, GRIB_MESSAGE)
        self.assertEqual(key, 'missingValue')
        self.assertTrue(fill_value < min_data or fill_value > max_data,
                        'Fill value {} is not outside data range '
                        '{} to {}.'.format(fill_value, min_data, max_data))
        return fill_value

    def assertValues(self, grib_api, values):
        # Check the correct data values have been set via:
        #   gribapi.grib_set_double_array(grib_message, 'values', ...)
        args, = grib_api.grib_set_double_array.call_args_list
        (message, key, values), kwargs = args
        self.assertIs(message, GRIB_MESSAGE)
        self.assertEqual(key, 'values')
        self.assertArrayEqual(values, values)
        self.assertEqual(kwargs, {})

    def test_simple(self):
        # Check the simple case of non-masked data with no scaling.
        cube = iris.cube.Cube(np.arange(5))
        grib_message = mock.sentinel.GRIB_MESSAGE
        with mock.patch(GRIB_API) as grib_api:
            data_section(cube, grib_message)
        # Check the use of a mask has been turned off.
        self.assertBitmapOff(grib_api)
        # Check the correct data values have been set.
        self.assertValues(grib_api, np.arange(5))

    def test_masked_with_finite_fill_value(self):
        cube = iris.cube.Cube(np.ma.MaskedArray([1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
                                                mask=[0, 0, 0, 1, 1, 1],
                                                fill_value=2000))
        grib_message = mock.sentinel.GRIB_MESSAGE
        with mock.patch(GRIB_API) as grib_api:
            data_section(cube, grib_message)
        # Check the use of a mask has been turned on.
        FILL = 2000
        self.assertBitmapOn(grib_api, FILL)
        # Check the correct data values have been set.
        self.assertValues(grib_api, [1, 2, 3, FILL, FILL, FILL])

    def test_masked_with_nan_fill_value(self):
        cube = iris.cube.Cube(np.ma.MaskedArray([1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
                                                mask=[0, 0, 0, 1, 1, 1],
                                                fill_value=np.nan))
        grib_message = mock.sentinel.GRIB_MESSAGE
        with mock.patch(GRIB_API) as grib_api:
            data_section(cube, grib_message)
        # Check the use of a mask has been turned on and a suitable fill
        # value has been chosen.
        FILL = self.assertBitmapRange(grib_api, 1, 3)
        # Check the correct data values have been set.
        self.assertValues(grib_api, [1, 2, 3, FILL, FILL, FILL])

    def test_scaled(self):
        # If the Cube's units don't match the units required by GRIB
        # ensure the data values are scaled correctly.
        cube = iris.cube.Cube(np.arange(5),
                              standard_name='geopotential_height', units='km')
        grib_message = mock.sentinel.GRIB_MESSAGE
        with mock.patch(GRIB_API) as grib_api:
            data_section(cube, grib_message)
        # Check the use of a mask has been turned off.
        self.assertBitmapOff(grib_api)
        # Check the correct data values have been set.
        self.assertValues(grib_api, np.arange(5) * 1000)

    def test_scaled_with_finite_fill_value(self):
        # When re-scaling masked data with a finite fill value, ensure
        # the fill value and any filled values are also re-scaled.
        cube = iris.cube.Cube(np.ma.MaskedArray([1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
                                                mask=[0, 0, 0, 1, 1, 1],
                                                fill_value=2000),
                              standard_name='geopotential_height', units='km')
        grib_message = mock.sentinel.GRIB_MESSAGE
        with mock.patch(GRIB_API) as grib_api:
            data_section(cube, grib_message)
        # Check the use of a mask has been turned on.
        FILL = 2000 * 1000
        self.assertBitmapOn(grib_api, FILL)
        # Check the correct data values have been set.
        self.assertValues(grib_api, [1000, 2000, 3000, FILL, FILL, FILL])

    def test_scaled_with_nan_fill_value(self):
        # When re-scaling masked data with a NaN fill value, ensure
        # a fill value is chosen which allows for the scaling, and any
        # filled values match the chosen fill value.
        cube = iris.cube.Cube(np.ma.MaskedArray([-1.0, 2.0, -1.0, 2.0],
                                                mask=[0, 0, 1, 1],
                                                fill_value=np.nan),
                              standard_name='geopotential_height', units='km')
        grib_message = mock.sentinel.GRIB_MESSAGE
        with mock.patch(GRIB_API) as grib_api:
            data_section(cube, grib_message)
        # Check the use of a mask has been turned on and a suitable fill
        # value has been chosen.
        FILL = self.assertBitmapRange(grib_api, -1000, 2000)
        # Check the correct data values have been set.
        self.assertValues(grib_api, [-1000, 2000, FILL, FILL])


class TestNonDoubleData(tests.IrisGribTest):
    # When saving to GRIB, data that is not float64 is cast to float64. This
    # test checks that non-float64 data is saved without raising a segmentation
    # fault.
    def check(self, dtype):
        data = np.random.random(1920 * 2560).astype(dtype)
        cube = iris.cube.Cube(data,
                              standard_name='geopotential_height', units='km')
        grib_message = gribapi.grib_new_from_samples("GRIB2")
        data_section(cube, grib_message)
        gribapi.grib_release(grib_message)

    def test_float32(self):
        self.check(dtype=np.float32)

    def test_int32(self):
        self.check(dtype=np.int32)

    def test_int64(self):
        self.check(dtype=np.int64)


if __name__ == "__main__":
    tests.main()
