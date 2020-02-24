# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Check that a GribMessage can be pickled."""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import pickle
import unittest

from iris.tests.integration.test_pickle import Common as PickleCommon

from iris_grib.message import GribMessage


@tests.skip_data
class TestPickleGribMessage(PickleCommon, tests.IrisGribTest):
    # NOTE: based on 'Common' from iris.tests.integration.test_pickle.
    def setUp(self):
        self.path = tests.get_data_path(("GRIB", "fp_units", "hours.grib2"))

    # NOTE: this looks like it is overriding the parent "pickle_cube", but this
    # function is *not* the same thing.
    # (a) the tests which use pickle_cube are "test_protocol_XXX", and none
    #     of those currently work (see overrides below).
    # (b) the tests which use *this* function are the extra ones below.
    #     These check only that a GribMessage, and its lazy ".data", can be
    #     pickled.  However, still, neither reads back successfully.
    # TODO: resolve this or remove the test.
    def pickle_obj(self, obj):
        with self.temp_filename(".pkl") as filename:
            with open(filename, "wb") as f:
                pickle.dump(obj, f)
            # NOTE: *ought* to read back + check equal, but it does not work.
            # TODO: fix

    # These probably "ought" to work, but currently fail.
    # see https://github.com/SciTools/iris-grib/issues/202
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
