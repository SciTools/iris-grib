# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for the `iris_grib.GribWrapper` class.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import numpy as np
from unittest import mock

from iris._lazy_data import is_lazy_data
from iris.exceptions import TranslationError

from iris_grib import GribWrapper, _load_generate


_message_length = 1000


def _mock_grib_get_long(grib_message, key):
    lookup = dict(totalLength=_message_length,
                  numberOfValues=200,
                  jPointsAreConsecutive=0,
                  Ni=20,
                  Nj=10,
                  edition=1)
    try:
        result = lookup[key]
    except KeyError:
        msg = 'Mock grib_get_long unknown key: {!r}'.format(key)
        raise AttributeError(msg)
    return result


def _mock_grib_get_string(grib_message, key):
    return grib_message


def _mock_grib_get_native_type(grib_message, key):
    result = int
    if key == 'gridType':
        result = str
    return result


class Test_edition(tests.IrisGribTest):
    def setUp(self):
        self.patch('iris_grib.GribWrapper._confirm_in_scope')
        self.patch('iris_grib.GribWrapper._compute_extra_keys')
        self.patch('gribapi.grib_get_long', _mock_grib_get_long)
        self.patch('gribapi.grib_get_string', _mock_grib_get_string)
        self.patch('gribapi.grib_get_native_type', _mock_grib_get_native_type)
        self.tell = mock.Mock(side_effect=[_message_length])

    def test_not_edition_1(self):
        def func(grib_message, key):
            return 2

        emsg = "GRIB edition 2 is not supported by 'GribWrapper'"
        with mock.patch('gribapi.grib_get_long', func):
            with self.assertRaisesRegex(TranslationError, emsg):
                GribWrapper(None)

    def test_edition_1(self):
        grib_message = 'regular_ll'
        grib_fh = mock.Mock(tell=self.tell)
        wrapper = GribWrapper(grib_message, grib_fh)
        self.assertEqual(wrapper.grib_message, grib_message)


@tests.skip_data
class Test_deferred_data(tests.IrisTest):
    def test_regular_data(self):
        filename = tests.get_data_path(('GRIB', 'gaussian',
                                        'regular_gg.grib1'))
        messages = list(_load_generate(filename))
        self.assertTrue(is_lazy_data(messages[0]._data))

    def test_reduced_data(self):
        filename = tests.get_data_path(('GRIB', 'reduced',
                                        'reduced_ll.grib1'))
        messages = list(_load_generate(filename))
        self.assertTrue(is_lazy_data(messages[0]._data))


class Test_deferred_proxy_args(tests.IrisTest):
    def setUp(self):
        self.patch('iris_grib.GribWrapper._confirm_in_scope')
        self.patch('iris_grib.GribWrapper._compute_extra_keys')
        self.patch('gribapi.grib_get_long', _mock_grib_get_long)
        self.patch('gribapi.grib_get_string', _mock_grib_get_string)
        self.patch('gribapi.grib_get_native_type', _mock_grib_get_native_type)
        tell_tale = np.arange(1, 5) * _message_length
        self.expected = tell_tale - _message_length
        self.grib_fh = mock.Mock(tell=mock.Mock(side_effect=tell_tale))
        self.dtype = np.float64
        self.path = self.grib_fh.name
        self.lookup = _mock_grib_get_long

    def test_regular_proxy_args(self):
        grib_message = 'regular_ll'
        shape = (self.lookup(grib_message, 'Nj'),
                 self.lookup(grib_message, 'Ni'))
        for offset in self.expected:
            with mock.patch('iris_grib.GribDataProxy') as mock_gdp:
                _ = GribWrapper(grib_message, self.grib_fh)
            mock_gdp.assert_called_once_with(shape, self.dtype,
                                             self.path, offset)

    def test_reduced_proxy_args(self):
        grib_message = 'reduced_gg'
        shape = (self.lookup(grib_message, 'numberOfValues'))
        for offset in self.expected:
            with mock.patch('iris_grib.GribDataProxy') as mock_gdp:
                _ = GribWrapper(grib_message, self.grib_fh)
            mock_gdp.assert_called_once_with((shape,), self.dtype,
                                             self.path, offset)


if __name__ == '__main__':
    tests.main()
