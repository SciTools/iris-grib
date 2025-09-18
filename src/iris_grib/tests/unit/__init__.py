# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""Unit tests for the :mod:`iris_grib` package."""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import eccodes
import numpy as np
from unittest import mock

import iris

import iris_grib
from iris_grib.message import GribMessage


def _make_test_message(sections):
    raw_message = mock.Mock(sections=sections)
    recreate_raw = mock.Mock(return_value=raw_message)
    return GribMessage(raw_message, recreate_raw)


def _mock_eccodes_fetch(message, key):
    """
    Fake the ecCodes key-fetch.

    Fetch key-value from the fake message (dictionary).
    If the key is not present, raise the diagnostic exception.

    """
    if key in message:
        return message[key]
    else:
        raise _mock_eccodes.CodesInternalError


def _mock_eccodes__codes_is_missing(grib_message, keyname):
    """
    Fake the ecCodes key-existence enquiry.

    Return whether the key exists in the fake message (dictionary).

    """
    return keyname not in grib_message


def _mock_eccodes__codes_get_native_type(grib_message, keyname):
    """
    Fake the ecCodes type-discovery operation.

    Return type of key-value in the fake message (dictionary).
    If the key is not present, raise the diagnostic exception.

    """
    if keyname in grib_message:
        return type(grib_message[keyname])
    raise _mock_eccodes.CodesInternalError(keyname)


# Construct a mock object to mimic the eccodes for GribWrapper testing.
_mock_eccodes = mock.Mock(spec=eccodes)
_mock_eccodes.CodesInternalError = Exception

_mock_eccodes.codes_get_long = mock.Mock(side_effect=_mock_eccodes_fetch)
_mock_eccodes.codes_get_string = mock.Mock(side_effect=_mock_eccodes_fetch)
_mock_eccodes.codes_get_double = mock.Mock(side_effect=_mock_eccodes_fetch)
_mock_eccodes.codes_get_double_array = mock.Mock(side_effect=_mock_eccodes_fetch)
_mock_eccodes.codes_is_missing = mock.Mock(side_effect=_mock_eccodes__codes_is_missing)
_mock_eccodes.codes_get_native_type = mock.Mock(
    side_effect=_mock_eccodes__codes_get_native_type
)


class FakeGribMessage(dict):
    """
    A 'fake grib message' object, for testing GribWrapper construction.

    Behaves as a dictionary, containing key-values for message keys.

    """

    def __init__(self, **kwargs):
        """
        Create a fake message object.

        General keys can be set/add as required via **kwargs.
        The 'time_code' key is specially managed.

        """
        # Start with a bare dictionary
        dict.__init__(self)
        # Extract specially-recognised keys.
        time_code = kwargs.pop("time_code", None)
        # Set the minimally required keys.
        self._init_minimal_message()
        # Also set a time-code, if given.
        if time_code is not None:
            self.set_timeunit_code(time_code)
        # Finally, add any remaining passed key-values.
        self.update(**kwargs)

    def _init_minimal_message(self):
        # Set values for all the required keys.
        self.update(
            {
                "edition": 1,
                "Ni": 1,
                "Nj": 1,
                "numberOfValues": 1,
                "alternativeRowScanning": 0,
                "centre": "ecmf",
                "year": 2007,
                "month": 3,
                "day": 23,
                "hour": 12,
                "minute": 0,
                "indicatorOfUnitOfTimeRange": 1,
                "gridType": "rotated_ll",
                "angleOfRotation": 0.0,
                "resolutionAndComponentFlags": 128,
                "iDirectionIncrementInDegrees": 0.036,
                "jDirectionIncrementInDegrees": 0.036,
                "iScansNegatively": 0,
                "jScansPositively": 1,
                "longitudeOfFirstGridPointInDegrees": -5.70,
                "latitudeOfFirstGridPointInDegrees": -4.452,
                "jPointsAreConsecutive": 0,
                "values": np.array([[1.0]]),
                "indicatorOfParameter": 9999,
                "parameterNumber": 9999,
                "startStep": 24,
                "timeRangeIndicator": 1,
                "P1": 2,
                "P2": 0,
                # time unit - needed AS WELL as 'indicatorOfUnitOfTimeRange'
                "unitOfTime": 1,
                "table2Version": 9999,
            }
        )

    def set_timeunit_code(self, timecode):
        self["indicatorOfUnitOfTimeRange"] = timecode
        # for some odd reason, GRIB1 code uses *both* of these
        # NOTE kludge -- the 2 keys are really the same thing
        self["unitOfTime"] = timecode


class TestField(tests.IrisGribTest):
    def _test_for_coord(
        self, field, convert, coord_predicate, expected_points, expected_bounds
    ):
        (
            _factories,
            _references,
            _standard_name,
            _long_name,
            _units,
            _attributes,
            _cell_methods,
            dim_coords_and_dims,
            aux_coords_and_dims,
        ) = convert(field)

        # Check for one and only one matching coordinate.
        coords_and_dims = dim_coords_and_dims + aux_coords_and_dims
        matching_coords = [
            coord for coord, _ in coords_and_dims if coord_predicate(coord)
        ]
        self.assertEqual(len(matching_coords), 1, str(matching_coords))
        coord = matching_coords[0]

        # Check points and bounds.
        if expected_points is not None:
            self.assertArrayEqual(coord.points, expected_points)

        if expected_bounds is None:
            self.assertIsNone(coord.bounds)
        else:
            self.assertArrayEqual(coord.bounds, expected_bounds)

    def assertCoordsAndDimsListsMatch(
        self, coords_and_dims_got, coords_and_dims_expected
    ):
        """
        Check that coords_and_dims lists are equivalent.

        The arguments are lists of pairs of (coordinate, dimensions).
        The elements are compared one-to-one, by coordinate name (so the order
        of the lists is _not_ significant).
        It also checks that the coordinate types (DimCoord/AuxCoord) match.

        """

        def sorted_by_coordname(list):
            return sorted(list, key=lambda item: item[0].name())

        coords_and_dims_got = sorted_by_coordname(coords_and_dims_got)
        coords_and_dims_expected = sorted_by_coordname(coords_and_dims_expected)
        self.assertEqual(coords_and_dims_got, coords_and_dims_expected)
        # Also check coordinate type equivalences (as Coord.__eq__ does not).
        self.assertEqual(
            [type(coord) for coord, dims in coords_and_dims_got],
            [type(coord) for coord, dims in coords_and_dims_expected],
        )


class TestGribSimple(tests.IrisGribTest):
    # A testing class that does not need the test data.
    def mock_grib(self):
        # A mock grib message, with attributes that can't be Mocks themselves.
        grib = mock.Mock()
        grib.startStep = 0
        grib.phenomenon_points = lambda unit: 3
        grib._forecastTimeUnit = "hours"
        grib.productDefinitionTemplateNumber = 0
        # define a level type (NB these 2 are effectively the same)
        grib.levelType = 1
        grib.typeOfFirstFixedSurface = 1
        grib.typeOfSecondFixedSurface = 1
        return grib

    def cube_from_message(self, grib):
        # Parameter translation now uses the GribWrapper, so we must convert
        # the Mock-based fake message to a FakeGribMessage.
        with mock.patch("iris_grib.eccodes", _mock_eccodes):
            grib_message = FakeGribMessage(**grib.__dict__)
            wrapped_msg = iris_grib.GribWrapper(grib_message)
            cube, _, _ = iris.fileformats.rules._make_cube(
                wrapped_msg, iris_grib._grib1_load_rules.grib1_convert
            )
        return cube
