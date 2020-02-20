# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration tests confirming that iris functionality is working with GRIB
files.
"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests


import pickle
import unittest

from iris.tests.integration.test_pickle import Common

from iris_grib.message import GribMessage


class TestPickleGribMessage(Common, tests.IrisGribTest):
    def setUp(self):
        self.path = tests.get_data_path(("GRIB", "fp_units", "hours.grib2"))

    def pickle_obj(self, obj):
        with self.temp_filename(".pkl") as filename:
            with open(filename, "wb") as f:
                pickle.dump(obj, f)

    # These probably "ought" to work, but currently fail.
    # see https://github.com/SciTools/iris/pull/2608
    @unittest.expectedFailure
    def test_protocol_0(self):
        super().test_protocol_0()

    @unittest.expectedFailure
    def test_protocol_1(self):
        super().test_protocol_1()

    @unittest.expectedFailure
    def test_protocol_2(self):
        super().test_protocol_2()

    def test(self):
        # Check that a GribMessage pickles without errors.
        messages = GribMessage.messages_from_filename(self.path)
        obj = next(messages)
        self.pickle_obj(obj)

    def test_data(self):
        # Check that GribMessage.data pickles without errors.
        messages = GribMessage.messages_from_filename(self.path)
        obj = next(messages).data
        self.pickle_obj(obj)


if __name__ == "__main__":
    tests.main()
