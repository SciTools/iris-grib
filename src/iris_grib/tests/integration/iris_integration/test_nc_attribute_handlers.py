# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Integration tests for reading/writing GRIB_PARAM attributes in netcdf files.

N.B. the relevant support code and classes (including testing) are all part of in Iris,
along with the ones for "STASH" and "ukmo__process_flags" ones.

But all the testing there is optional, and skipped if iris-grib is not installed, so
that the Iris repo doesn't have to maintain iris-grib as a test dependency.

So, we import + run the relevant tests here instead.

"""

import pytest

# Start by attempting the key imports from Iris, and skipping all tests if any fail.
# Needed to run with older Iris (releases) prior to the tests being added.
# Unfortunately we can't actually use the returned items, as dynamic typing upsets MyPy.
pytest.importorskip("iris.tests.integration.netcdf.test_load_managed_attributes")
pytest.importorskip("iris.tests.integration.netcdf.test_save_managed_attributes")
pytest.importorskip("iris.tests.unit.fileformats.netcdf.attribute_handlers")


from iris.tests.integration.netcdf.test_load_managed_attributes import (
    TestGribParam as LoadGribParamTests,
)

from iris.tests.integration.netcdf.test_save_managed_attributes import (
    TestGribParam as SaveGribParamTests,
)

from iris.tests.unit.fileformats.netcdf.attribute_handlers import (
    test_GribParamHandler as tgp,
)


class TestLoadGribParam_actual(LoadGribParamTests):
    pass


class TestSaveGribParam_actual(SaveGribParamTests):
    pass


class TestGribParamHandler_Encode(tgp.TestEncodeObject):
    pass


class TestGribParamHandler_Decode(tgp.TestDecodeAttribute):
    pass
