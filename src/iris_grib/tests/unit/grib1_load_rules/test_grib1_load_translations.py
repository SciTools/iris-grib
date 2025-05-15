# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Tests for specific implementation aspects of the grib loaders.
Old, and GRIB-1 specific.
Ported here from 'iris.tests.test_grib_load_translations'.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else
import iris_grib.tests as tests

import datetime
from unittest import mock

import cf_units
import numpy as np

import iris
import iris.exceptions

import eccodes
import iris.fileformats
import iris_grib


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


# Construct a mock object to mimic the ecCodes for GribWrapper testing.
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

# define seconds in an hour, for general test usage
_hour_secs = 3600.0


class FakeGribMessage(dict):
    """
    A 'fake grib message' object, for testing GribWrapper construction.

    Behaves as a dictionary, containing key-values for message keys.

    """

    def __init__(self, **kwargs):
        """
        Create a fake message object.

        General keys can be set/add as required via **kwargs.
        The keys 'edition' and 'time_code' are specially managed.

        """
        # Start with a bare dictionary
        dict.__init__(self)
        # Extract specially-recognised keys.
        edition = kwargs.pop("edition", 1)
        # This testing is only for old-style Grib-1 code.
        assert edition == 1
        time_code = kwargs.pop("time_code", None)
        # Set the minimally required keys.
        self._init_minimal_message(edition=edition)
        # Also set a time-code, if given.
        if time_code is not None:
            self.set_timeunit_code(time_code)
        # Finally, add any remaining passed key-values.
        self.update(**kwargs)

    def _init_minimal_message(self, edition=1):
        # Set values for all the required keys.
        # 'edition' controls the edition-specific keys.
        self.update(
            {
                "Ni": 1,
                "Nj": 1,
                "numberOfValues": 1,
                "alternativeRowScanning": 0,
                "centre": 74,  # the UKMO centre id
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
        # Add edition-dependent settings.
        self["edition"] = edition

    def set_timeunit_code(self, timecode):
        # Do timecode setting (somewhat edition-dependent).
        self["indicatorOfUnitOfTimeRange"] = timecode
        # for some odd reason, GRIB1 code uses *both* of these
        # NOTE kludge -- the 2 keys are really the same thing
        self["unitOfTime"] = timecode


class TestGribTimecodes(tests.IrisTest):
    def _run_timetests(self, test_set):
        # Check the unit-handling for given units-codes and editions.

        # Operates on lists of cases for various time-units and grib-editions.
        # Format: (edition, code, expected-exception,
        #          equivalent-seconds, description-string)
        with mock.patch("iris_grib.eccodes", _mock_eccodes):
            for test_controls in test_set:
                (
                    grib_edition,
                    timeunit_codenum,
                    expected_error,
                    timeunit_secs,
                    timeunit_str,
                ) = test_controls

                # Construct a suitable fake test message.
                message = FakeGribMessage(
                    edition=grib_edition, time_code=timeunit_codenum
                )

                if expected_error:
                    # Expect GribWrapper construction to fail.
                    with self.assertRaises(type(expected_error)) as ar_context:
                        _ = iris_grib.GribWrapper(message)
                    self.assertEqual(ar_context.exception.args, expected_error.args)
                    continue

                # 'ELSE'...
                # Expect the wrapper construction to work.
                # Make a GribWrapper object and test it.
                wrapped_msg = iris_grib.GribWrapper(message)

                # Check the units string.
                forecast_timeunit = wrapped_msg._forecastTimeUnit
                self.assertEqual(
                    forecast_timeunit,
                    timeunit_str,
                    "Bad unit string for edition={ed:01d}, "
                    "unitcode={code:01d} : "
                    'expected="{wanted}" GOT="{got}"'.format(
                        ed=grib_edition,
                        code=timeunit_codenum,
                        wanted=timeunit_str,
                        got=forecast_timeunit,
                    ),
                )

                # Check the data-starttime calculation.
                interval_start_to_end = (
                    wrapped_msg._phenomenonDateTime - wrapped_msg._referenceDateTime
                )
                if grib_edition == 1:
                    interval_from_units = wrapped_msg.P1
                else:
                    interval_from_units = wrapped_msg.forecastTime
                interval_from_units *= datetime.timedelta(0, timeunit_secs)
                self.assertEqual(
                    interval_start_to_end,
                    interval_from_units,
                    "Inconsistent start time offset for edition={ed:01d}, "
                    "unitcode={code:01d} : "
                    'from-unit="{unit_str}" '
                    'from-phenom-minus-ref="{e2e_str}"'.format(
                        ed=grib_edition,
                        code=timeunit_codenum,
                        unit_str=interval_from_units,
                        e2e_str=interval_start_to_end,
                    ),
                )

    # Test groups of testcases for various time-units and grib-editions.
    # Format: (edition, code, expected-exception,
    #          equivalent-seconds, description-string)
    def test_timeunits_common(self):
        tests = (
            (1, 0, None, 60.0, "minutes"),
            (1, 1, None, _hour_secs, "hours"),
            (1, 2, None, 24.0 * _hour_secs, "days"),
            (1, 10, None, 3.0 * _hour_secs, "3 hours"),
            (1, 11, None, 6.0 * _hour_secs, "6 hours"),
            (1, 12, None, 12.0 * _hour_secs, "12 hours"),
        )
        TestGribTimecodes._run_timetests(self, tests)

    @staticmethod
    def _err_bad_timeunit(code):
        return iris.exceptions.NotYetImplementedError(
            "Unhandled time unit for forecast "
            "indicatorOfUnitOfTimeRange : {code}".format(code=code)
        )

    def test_timeunits_grib1_specific(self):
        tests = (
            (1, 13, None, 0.25 * _hour_secs, "15 minutes"),
            (1, 14, None, 0.5 * _hour_secs, "30 minutes"),
            (1, 254, None, 1.0, "seconds"),
            (1, 111, TestGribTimecodes._err_bad_timeunit(111), 1.0, "??"),
        )
        TestGribTimecodes._run_timetests(self, tests)

    def test_timeunits_calendar(self):
        tests = (
            (1, 3, TestGribTimecodes._err_bad_timeunit(3), 0.0, "months"),
            (1, 4, TestGribTimecodes._err_bad_timeunit(4), 0.0, "years"),
            (1, 5, TestGribTimecodes._err_bad_timeunit(5), 0.0, "decades"),
            (1, 6, TestGribTimecodes._err_bad_timeunit(6), 0.0, "30 years"),
            (1, 7, TestGribTimecodes._err_bad_timeunit(7), 0.0, "centuries"),
        )
        TestGribTimecodes._run_timetests(self, tests)

    def test_timeunits_invalid(self):
        tests = ((1, 111, TestGribTimecodes._err_bad_timeunit(111), 1.0, "??"),)
        TestGribTimecodes._run_timetests(self, tests)

    def test_warn_unknown_pdts(self):
        # Test loading of an unrecognised GRIB Product Definition Template.

        # Get a temporary file by name (deleted afterward by context).
        with self.temp_filename() as temp_gribfile_path:
            # Write a test grib message to the temporary file.
            with open(temp_gribfile_path, "wb") as temp_gribfile:
                grib_message = eccodes.codes_grib_new_from_samples("GRIB2")
                # Set the PDT to something unexpected.
                eccodes.codes_set_long(
                    grib_message, "productDefinitionTemplateNumber", 99
                )
                eccodes.codes_write(grib_message, temp_gribfile)

            # Load the message from the file as a cube.
            cube_generator = iris_grib.load_cubes(temp_gribfile_path)
            with self.assertRaises(iris.exceptions.TranslationError) as t_err:
                _ = next(cube_generator)
            self.assertEqual(
                "Product definition template [99] is not supported",
                str(t_err.exception),
            )


class TestGrib1LoadPhenomenon(tests.IrisTest):
    # Test recognition of grib phenomenon types.
    def mock_grib(self):
        grib = mock.Mock()
        grib.edition = 1
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

    def test_grib1_unknownparam(self):
        grib = self.mock_grib()
        grib.table2Version = 0
        grib.indicatorOfParameter = 9999
        cube = self.cube_from_message(grib)
        self.assertEqual(cube.standard_name, None)
        self.assertEqual(cube.long_name, None)
        self.assertEqual(cube.units, cf_units.Unit("???"))

    def test_grib1_unknown_local_param(self):
        grib = self.mock_grib()
        grib.table2Version = 128
        grib.indicatorOfParameter = 999
        cube = self.cube_from_message(grib)
        self.assertEqual(cube.standard_name, None)
        self.assertEqual(cube.long_name, "UNKNOWN LOCAL PARAM 999.128")
        self.assertEqual(cube.units, cf_units.Unit("???"))

    def test_grib1_unknown_standard_param(self):
        grib = self.mock_grib()
        grib.table2Version = 1
        grib.indicatorOfParameter = 975
        cube = self.cube_from_message(grib)
        self.assertEqual(cube.standard_name, None)
        self.assertEqual(cube.long_name, "UNKNOWN LOCAL PARAM 975.1")
        self.assertEqual(cube.units, cf_units.Unit("???"))

    def known_grib1(self, param, standard_str, units_str):
        grib = self.mock_grib()
        grib.table2Version = 1
        grib.indicatorOfParameter = param
        cube = self.cube_from_message(grib)
        self.assertEqual(cube.standard_name, standard_str)
        self.assertEqual(cube.long_name, None)
        self.assertEqual(cube.units, cf_units.Unit(units_str))

    def test_grib1_known_standard_params(self):
        # at present, there are just a very few of these
        self.known_grib1(11, "air_temperature", "kelvin")
        self.known_grib1(33, "x_wind", "m s-1")
        self.known_grib1(34, "y_wind", "m s-1")


if __name__ == "__main__":
    tests.main()
