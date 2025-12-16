# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Unit tests for the :class:`iris_grib.Grib1LoadingMode` class.
"""

import pytest

from iris_grib import Grib1LoadingMode


@pytest.fixture(autouse=True)
def mode_obj():
    test_object = Grib1LoadingMode()
    return test_object


class TestInit:
    def test_default(self):
        result = Grib1LoadingMode()
        assert result.use_legacy_grib1_loading

    def test_kwarg(self):
        result = Grib1LoadingMode(legacy=False)
        assert not result.use_legacy_grib1_loading

    def test_arg_fail(self):
        msg = "takes 1 positional argument but 2 were given"
        with pytest.raises(TypeError, match=msg):
            Grib1LoadingMode(1)


class TestLegacyProperty:
    def test_get_legacy(self, mode_obj):
        assert mode_obj.use_legacy_grib1_loading

    def test_set_legacy_fail(self, mode_obj):
        msg1 = "'use_legacy_grib1_loading' of 'Grib1LoadingMode' object has no setter"
        # NOTE: message was different in Python <= 3.10
        msg2 = "can't set attribute 'use_legacy_grib1_loading'"
        try:
            mode_obj.use_legacy_grib1_loading = False
        except AttributeError as err:
            result = str(err)
        assert msg1 in result or msg2 in result


class TestSet:
    def test_set_unset(self, mode_obj):
        assert mode_obj.use_legacy_grib1_loading
        mode_obj.set(legacy=False)
        assert not mode_obj.use_legacy_grib1_loading
        mode_obj.set(legacy=True)
        assert mode_obj.use_legacy_grib1_loading

    def test_arg_fail(self, mode_obj):
        msg = "takes 1 positional argument but 2 were given"
        with pytest.raises(TypeError, match=msg):
            mode_obj.set(False)


class TestContext:
    def test_context(self, mode_obj):
        assert mode_obj.use_legacy_grib1_loading
        with mode_obj.context(legacy=False):
            assert not mode_obj.use_legacy_grib1_loading
            with mode_obj.context(legacy=True):
                assert mode_obj.use_legacy_grib1_loading

            assert not mode_obj.use_legacy_grib1_loading

        assert mode_obj.use_legacy_grib1_loading

    def test_arg_fail(self, mode_obj):
        msg = "takes 1 positional argument but 2 were given"
        with pytest.raises(TypeError, match=msg):
            mode_obj.context(False)


class TestStrRepr:
    @pytest.mark.parametrize("func", ["str", "repr"])
    def test_strrepr(self, mode_obj, func):
        func = {"str": str, "repr": repr}[func]
        result = func(mode_obj)
        assert result == "GRIB1_LOADING_MODE(legacy=True)"
        mode_obj.set(legacy=False)
        result2 = func(mode_obj)
        assert result2 == "GRIB1_LOADING_MODE(legacy=False)"
