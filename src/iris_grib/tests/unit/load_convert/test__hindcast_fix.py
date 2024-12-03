# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Tests for function :func:`iris_grib._load_convert._hindcast_fix`.

"""

from collections import namedtuple
import warnings

import pytest

from iris_grib._load_convert import _hindcast_fix as hindcast_fix
from iris_grib._load_convert import HindcastOverflowWarning


FixTest = namedtuple("FixTest", ("given", "fixable", "fixed"))
HINDCAST_TESTCASES = {
    "zero_x": FixTest(0, False, None),
    "n100_x": FixTest(100, False, None),
    "n2^31m1_x": FixTest(2 * 2**30 - 1, False, None),
    "n2^31_x": FixTest(2 * 2**30, False, None),
    "n2^31p1_m1": FixTest(2 * 2**30 + 1, True, -1),
    "n2^31p2_m2": FixTest(2 * 2**30 + 2, True, -2),
    "n3x2^30m1_m2^30m1": FixTest(3 * 2**30 - 1, True, -(2**30 - 1)),
    "n3x2^30^30_x": FixTest(3 * 2**30, False, None),
}


class TestHindcastFix:
    @pytest.mark.parametrize(
        "testval",
        list(HINDCAST_TESTCASES.values()),
        ids=list(HINDCAST_TESTCASES.keys()),
    )
    def test_fix(self, testval):
        # Check hindcast fixing.
        given, fixable, fixed = testval
        result = hindcast_fix(given)
        expected = fixed if fixable else given
        assert result == expected

    def test_fix_warning(self, mocker):
        # Check warning appears when enabled.
        mocker.patch("iris_grib._load_convert.options.warn_on_unsupported", True)
        msg = "Re-interpreting large grib forecastTime"
        with pytest.warns(HindcastOverflowWarning, match=msg):
            hindcast_fix(2 * 2**30 + 5)

    def test_fix_warning_disabled(self):
        # Default is no warning.
        with warnings.catch_warnings():
            warnings.simplefilter(category=HindcastOverflowWarning, action="error")
            hindcast_fix(2 * 2**30 + 5)
