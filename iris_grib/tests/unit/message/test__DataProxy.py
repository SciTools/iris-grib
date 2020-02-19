# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for the `iris.message._DataProxy` class.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

import numpy as np
from numpy.random import randint

from iris.exceptions import TranslationError

from iris_grib.message import _DataProxy


class Test__bitmap(tests.IrisGribTest):
    def test_no_bitmap(self):
        section_6 = {'bitMapIndicator': 255, 'bitmap': None}
        data_proxy = _DataProxy(0, 0, 0)
        result = data_proxy._bitmap(section_6)
        self.assertIsNone(result)

    def test_bitmap_present(self):
        bitmap = randint(2, size=(12))
        section_6 = {'bitMapIndicator': 0, 'bitmap': bitmap}
        data_proxy = _DataProxy(0, 0, 0)
        result = data_proxy._bitmap(section_6)
        self.assertArrayEqual(bitmap, result)

    def test_bitmap__invalid_indicator(self):
        section_6 = {'bitMapIndicator': 100, 'bitmap': None}
        data_proxy = _DataProxy(0, 0, 0)
        with self.assertRaisesRegex(TranslationError, 'unsupported bitmap'):
            data_proxy._bitmap(section_6)


class Test_emptyfetch(tests.IrisGribTest):
    # See : 
    #   iris.tests.unit.fileformats.pp.test_PPDataProxy.Test__getitem__slicing
    # In this case, test *only* the no-data-read effect, not the method which
    # is part of Iris.
    def test_empty_slice(self):
        # Check behaviour of the getitem call with an 'empty' slicing.
        # This is necessary because, since Dask 2.0, the "from_array" function
        # takes a zero-length slice of its array argument, to capture array
        # metadata, and in those cases we want to avoid file access.
        test_dtype = np.dtype(np.float32)
        mock_datafetch = mock.MagicMock()
        proxy = _DataProxy(shape=(3, 4),
                           dtype=np.dtype(np.float32),
                           recreate_raw=mock_datafetch)

        # Test the special no-data indexing operation.
        result = proxy[0:0, 0:0]

        # Check the behaviour and results were as expected.
        self.assertEqual(mock_datafetch.call_count, 0)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.dtype, test_dtype)
        self.assertEqual(result.shape, (0, 0))


if __name__ == '__main__':
    tests.main()
