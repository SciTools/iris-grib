# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Unit tests for the `iris_grib.save_messages` function."""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import gribapi
from unittest import mock

import iris_grib


class TestSaveMessages(tests.IrisGribTest):
    def setUp(self):
        # Create a test object to stand in for a real PPField.
        self.grib_message = gribapi.grib_new_from_samples("GRIB2")

    def test_save(self):
        m = mock.mock_open()
        with mock.patch('builtins.open', m, create=True):
            iris_grib.save_messages([self.grib_message], 'foo.grib2')
        self.assertTrue(mock.call('foo.grib2', 'wb') in m.mock_calls)

    def test_save_append(self):
        m = mock.mock_open()
        with mock.patch('builtins.open', m, create=True):
            iris_grib.save_messages([self.grib_message], 'foo.grib2',
                                    append=True)
        self.assertTrue(mock.call('foo.grib2', 'ab') in m.mock_calls)


if __name__ == "__main__":
    tests.main()
