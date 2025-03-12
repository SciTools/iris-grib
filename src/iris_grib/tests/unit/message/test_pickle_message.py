# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""Check that a GribMessage can be pickled."""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import pickle

import pytest
from iris_grib.message import GribMessage

MIN_PICKLE_PROTOCOL = 4

TESTED_PROTOCOLS = list(range(MIN_PICKLE_PROTOCOL, pickle.HIGHEST_PROTOCOL + 1))


@tests.skip_data
class TestPickleGribMessage:
    @pytest.fixture
    def messages(self):
        path = tests.get_data_path(("GRIB", "fp_units", "hours.grib2"))
        return GribMessage.messages_from_filename(path)

    def pickle_obj(self, obj, protocol, tmp_path):
        # NOTE: Neither GribMessage, nor its lazy ".data", read back from
        # a pickled obj. Currently, this only checks that they can be pickled
        # successfully.
        filename = tmp_path / ".pkl"
        with open(filename, "wb") as f:
            pickle.dump(obj, f, protocol)
        # TODO: resolve this or remove the test.
        #  with open(filename, "rb") as f:
        #      nobj = pickle.load(f)
        #  assert nobj == obj

    @pytest.mark.parametrize("protocol", TESTED_PROTOCOLS)
    def test_message(self, protocol, messages, tmp_path):
        obj = next(messages)
        self.pickle_obj(obj, protocol, tmp_path)

    @pytest.mark.parametrize("protocol", TESTED_PROTOCOLS)
    def test_message_data(self, protocol, messages, tmp_path):
        obj = next(messages).data
        self.pickle_obj(obj, protocol, tmp_path)
