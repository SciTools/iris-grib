# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Test function
:func:`iris_grib._load_convert.grid_definition_template_4_and_5`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from copy import deepcopy
from unittest import mock
import warnings

from iris.coords import DimCoord
import numpy as np

from iris_grib._load_convert import grid_definition_template_4_and_5, _MDI as MDI


RESOLUTION = 1e6


class Test(tests.IrisGribTest):
    def setUp(self):
        self.patch("warnings.warn")
        self.patch("iris_grib._load_convert._is_circular", return_value=False)
        self.metadata = {
            "factories": [],
            "references": [],
            "standard_name": None,
            "long_name": None,
            "units": None,
            "attributes": {},
            "cell_methods": [],
            "dim_coords_and_dims": [],
            "aux_coords_and_dims": [],
        }
        self.cs = mock.sentinel.coord_system
        self.data = np.arange(10, dtype=np.float64)

    def _check(self, section, request_warning, expect_warning=False, y_dim=0, x_dim=1):
        this = "iris_grib._load_convert.options"
        with mock.patch(this, warn_on_unsupported=request_warning):
            metadata = deepcopy(self.metadata)
            # The called being tested.
            grid_definition_template_4_and_5(
                section, metadata, "latitude", "longitude", self.cs
            )
            expected = deepcopy(self.metadata)
            coord = DimCoord(
                self.data,
                standard_name="latitude",
                units="degrees",
                coord_system=self.cs,
            )
            expected["dim_coords_and_dims"].append((coord, y_dim))
            coord = DimCoord(
                self.data,
                standard_name="longitude",
                units="degrees",
                coord_system=self.cs,
            )
            expected["dim_coords_and_dims"].append((coord, x_dim))
            self.assertEqual(metadata, expected)
            if expect_warning:
                self.assertEqual(len(warnings.warn.mock_calls), 1)
                args, _kwargs = warnings.warn.call_args
                self.assertIn("resolution and component flags", args[0])
            else:
                self.assertEqual(len(warnings.warn.mock_calls), 0)

    def test_resolution_default_0(self):
        for request_warn in [False, True]:
            section = {
                "basicAngleOfTheInitialProductionDomain": 0,
                "subdivisionsOfBasicAngle": 0,
                "resolutionAndComponentFlags": 0,
                "longitudes": self.data * RESOLUTION,
                "latitudes": self.data * RESOLUTION,
                "scanningMode": 0,
            }
            self._check(section, request_warn)

    def test_resolution_default_mdi(self):
        for request_warn in [False, True]:
            section = {
                "basicAngleOfTheInitialProductionDomain": MDI,
                "subdivisionsOfBasicAngle": MDI,
                "resolutionAndComponentFlags": 0,
                "longitudes": self.data * RESOLUTION,
                "latitudes": self.data * RESOLUTION,
                "scanningMode": 0,
            }
            self._check(section, request_warn)

    def test_resolution(self):
        angle = 10
        for request_warn in [False, True]:
            section = {
                "basicAngleOfTheInitialProductionDomain": 1,
                "subdivisionsOfBasicAngle": angle,
                "resolutionAndComponentFlags": 0,
                "longitudes": self.data * angle,
                "latitudes": self.data * angle,
                "scanningMode": 0,
            }
            self._check(section, request_warn)

    def test_uv_resolved_warn(self):
        angle = 100
        for warn in [False, True]:
            section = {
                "basicAngleOfTheInitialProductionDomain": 1,
                "subdivisionsOfBasicAngle": angle,
                "resolutionAndComponentFlags": 0x08,
                "longitudes": self.data * angle,
                "latitudes": self.data * angle,
                "scanningMode": 0,
            }
            self._check(section, warn, expect_warning=warn)

    def test_j_consecutive(self):
        angle = 1000
        for request_warn in [False, True]:
            section = {
                "basicAngleOfTheInitialProductionDomain": 1,
                "subdivisionsOfBasicAngle": angle,
                "resolutionAndComponentFlags": 0,
                "longitudes": self.data * angle,
                "latitudes": self.data * angle,
                "scanningMode": 0x20,
            }
            self._check(section, request_warn, y_dim=1, x_dim=0)


if __name__ == "__main__":
    tests.main()
