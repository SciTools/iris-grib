# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Test function :func:`iris_grib._load_convert.vertical_coords`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from copy import deepcopy
from unittest import mock

from iris.coords import DimCoord
from iris.exceptions import TranslationError

from iris_grib._load_convert import vertical_coords
from iris_grib._load_convert import (
    _TYPE_OF_FIXED_SURFACE_MISSING as MISSING_SURFACE,
    _MDI as MISSING_LEVEL,
)


class Test(tests.IrisGribTest):
    def setUp(self):
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

    def test_hybrid_factories(self):
        def func(section, metadata):
            return metadata["factories"].append(factory)

        metadata = deepcopy(self.metadata)
        section = {"NV": 1}
        this = "iris_grib._load_convert.hybrid_factories"
        factory = mock.sentinel.factory
        with mock.patch(this, side_effect=func) as hybrid_factories:
            vertical_coords(section, metadata)
            self.assertTrue(hybrid_factories.called)
            self.assertEqual(metadata["factories"], [factory])

    def test_no_first_fixed_surface(self):
        metadata = deepcopy(self.metadata)
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": MISSING_SURFACE,
            "scaledValueOfFirstFixedSurface": MISSING_LEVEL,
        }
        vertical_coords(section, metadata)
        self.assertEqual(metadata, self.metadata)

    def test_fixed_surface_type_1(self):
        metadata = deepcopy(self.metadata)
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 1,
            "scaledValueOfFirstFixedSurface": 0,
            "scaleFactorOfFirstFixedSurface": 0,
            "typeOfSecondFixedSurface": 255,
        }
        vertical_coords(section, metadata)
        # No metadata change, as surfaceType=1 translates to "no vertical
        # coord" without error or warning.
        self.assertEqual(metadata, self.metadata)

    def test_unknown_first_fixed_surface_with_missing_scaled_value(self):
        this = "iris_grib._load_convert.options"
        with mock.patch("warnings.warn") as warn:
            with mock.patch(this) as options:
                for request_warning in [False, True]:
                    options.warn_on_unsupported = request_warning
                    metadata = deepcopy(self.metadata)
                    section = {
                        "NV": 0,
                        "typeOfFirstFixedSurface": 0,
                        "scaledValueOfFirstFixedSurface": MISSING_LEVEL,
                    }
                    # The call being tested.
                    vertical_coords(section, metadata)
                    self.assertEqual(metadata, self.metadata)
                    if request_warning:
                        self.assertEqual(len(warn.mock_calls), 1)
                        args, _ = warn.call_args
                        self.assertIn("surface with missing scaled value", args[0])
                    else:
                        self.assertEqual(len(warn.mock_calls), 0)

    def test_unknown_first_fixed_surface(self):
        metadata = deepcopy(self.metadata)
        expected = deepcopy(self.metadata)
        coord = DimCoord(600.0, attributes={"GRIB_fixed_surface_type": 106})
        expected["aux_coords_and_dims"].append((coord, None))

        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 106,
            "scaledValueOfFirstFixedSurface": 600,
            "scaleFactorOfFirstFixedSurface": 0,
            "typeOfSecondFixedSurface": MISSING_SURFACE,
        }
        vertical_coords(section, metadata)
        self.assertEqual(metadata, expected)

    def test_unknown_first_fixed_surface_with_second_fixed_surface(self):
        metadata = deepcopy(self.metadata)
        expected = deepcopy(self.metadata)
        coord = DimCoord(
            9000.0, bounds=[18000, 0], attributes={"GRIB_fixed_surface_type": 108}
        )
        expected["aux_coords_and_dims"].append((coord, None))

        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 108,
            "scaledValueOfFirstFixedSurface": 18000,
            "scaleFactorOfFirstFixedSurface": 0,
            "typeOfSecondFixedSurface": 108,
            "scaledValueOfSecondFixedSurface": 0,
            "scaleFactorOfSecondFixedSurface": 0,
        }
        vertical_coords(section, metadata)
        self.assertEqual(metadata, expected)

    def test_pressure_with_no_second_fixed_surface(self):
        metadata = deepcopy(self.metadata)
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 100,  # pressure / Pa
            "scaledValueOfFirstFixedSurface": 10,
            "scaleFactorOfFirstFixedSurface": 1,
            "typeOfSecondFixedSurface": MISSING_SURFACE,
        }
        vertical_coords(section, metadata)
        coord = DimCoord(1.0, long_name="pressure", units="Pa")
        expected = deepcopy(self.metadata)
        expected["aux_coords_and_dims"].append((coord, None))
        self.assertEqual(metadata, expected)

    def test_height_with_no_second_fixed_surface(self):
        metadata = deepcopy(self.metadata)
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 103,  # height / m
            "scaledValueOfFirstFixedSurface": 100,
            "scaleFactorOfFirstFixedSurface": 2,
            "typeOfSecondFixedSurface": MISSING_SURFACE,
        }
        vertical_coords(section, metadata)
        coord = DimCoord(1.0, long_name="height", units="m")
        expected = deepcopy(self.metadata)
        expected["aux_coords_and_dims"].append((coord, None))
        self.assertEqual(metadata, expected)

    def test_different_fixed_surfaces_same_parameter(self):
        metadata = deepcopy(self.metadata)
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 103,
            "scaledValueOfFirstFixedSurface": 10,
            "scaleFactorOfFirstFixedSurface": 1,
            "typeOfSecondFixedSurface": 1,
        }
        vertical_coords(section, metadata)
        coord = DimCoord(0.5, long_name="height", units="m", bounds=[1.0, 0.0])
        expected = deepcopy(self.metadata)
        expected["aux_coords_and_dims"].append((coord, None))
        self.assertEqual(metadata, expected)

    def test_different_fixed_surfaces_different_parameter(self):
        metadata = deepcopy(self.metadata)
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 100,
            "scaledValueOfFirstFixedSurface": 10,
            "scaleFactorOfFirstFixedSurface": 1,
            "typeOfSecondFixedSurface": 1,
        }
        vertical_coords(section, metadata)
        coords = [
            DimCoord(1.0, long_name="pressure", units="Pa"),
            DimCoord(0.0, long_name="height", units="m"),
        ]
        expected = deepcopy(self.metadata)
        [expected["aux_coords_and_dims"].append((coord, None)) for coord in coords]
        self.assertEqual(metadata, expected)

    def test_same_fixed_surfaces_missing_second_scaled_value(self):
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 100,
            "scaledValueOfFirstFixedSurface": 10,
            "scaleFactorOfFirstFixedSurface": 1,
            "typeOfSecondFixedSurface": 100,
            "scaledValueOfSecondFixedSurface": MISSING_LEVEL,
        }
        emsg = (
            "Unable to translate type of Second fixed surface with missing scaled "
            "value."
        )
        with self.assertRaisesRegex(TranslationError, emsg):
            vertical_coords(section, None)

    def test_pressure_with_second_fixed_surface(self):
        metadata = deepcopy(self.metadata)
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 100,
            "scaledValueOfFirstFixedSurface": 10,
            "scaleFactorOfFirstFixedSurface": 1,
            "typeOfSecondFixedSurface": 100,
            "scaledValueOfSecondFixedSurface": 30,
            "scaleFactorOfSecondFixedSurface": 1,
        }
        vertical_coords(section, metadata)
        coord = DimCoord(2.0, long_name="pressure", units="Pa", bounds=[1.0, 3.0])
        expected = deepcopy(self.metadata)
        expected["aux_coords_and_dims"].append((coord, None))
        self.assertEqual(metadata, expected)

    def test_height_with_second_fixed_surface(self):
        metadata = deepcopy(self.metadata)
        section = {
            "NV": 0,
            "typeOfFirstFixedSurface": 103,
            "scaledValueOfFirstFixedSurface": 1000,
            "scaleFactorOfFirstFixedSurface": 2,
            "typeOfSecondFixedSurface": 103,
            "scaledValueOfSecondFixedSurface": 3000,
            "scaleFactorOfSecondFixedSurface": 2,
        }
        vertical_coords(section, metadata)
        coord = DimCoord(20.0, long_name="height", units="m", bounds=[10.0, 30.0])
        expected = deepcopy(self.metadata)
        expected["aux_coords_and_dims"].append((coord, None))
        self.assertEqual(metadata, expected)


if __name__ == "__main__":
    tests.main()
