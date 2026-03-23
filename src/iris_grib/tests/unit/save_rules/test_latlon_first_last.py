# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""Unit tests for `iris_grib.grib_save_rules.identification`."""

import numpy as np

from iris.coords import AuxCoord

from iris_grib._save_rules import latlon_first_last


class Test:
    """Check operation for specific test values.

    The specific point is that coord values should be promoted to "double" to optimise
    rounding error when converting to integer.
    In effect, this was the default with numpy 1, but changed in numpy 2.
    See : https://github.com/SciTools/iris-grib/issues/686
    """

    # Numbers from a real testcase, where naive non-promoted calculation got it "wrong".
    lbrow = 1920
    lbnpt = 2560
    bzx = -0.070312500000000000000000000000
    bdx = 0.140625000000000000000000000000
    bzy = -90.046875000000000000000000000000
    bdy = 0.093750000000000000000000000000

    def test_lats(self, mocker):
        patch = mocker.patch("iris_grib._save_rules.eccodes.codes_set_long")
        x_points = np.array(
            [self.bzx + self.bdx, self.bzx + self.lbnpt * self.bdx], dtype=np.float32
        )
        y_points = np.array(
            [self.bzy + self.bdy, self.bzy + self.lbrow * self.bdy], dtype=np.float32
        )
        x_coord = AuxCoord(x_points)
        y_coord = AuxCoord(y_points)
        latlon_first_last(x_coord, y_coord, None)
        cal = patch.call_args_list
        assert len(cal) == 4
        results = [call.args[2] for call in cal]
        expected = [-89953125, 89953125, 70312, 359929687]
        assert results == expected
