# (C) British Crown Copyright 2014 - 2016, Met Office
#
# This file is part of iris-grib.
#
# iris-grib is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-grib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-grib.  If not, see <http://www.gnu.org/licenses/>.
'''
Unit tests for timecode handling in the the
mod:`iris_grib.grib_phenom_translation` module.

Carried over from old iris/tests/test_grib_phenom_translation.py.
Code is out of step with current test conventions and standards.

'''
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import cf_units
import datetime
import gribapi

import iris_grib.grib_phenom_translation as gptx
import numpy as np

from iris.exceptions import NotYetImplementedError, TranslationError
from iris_grib import GribWrapper
from iris_grib import load_cubes

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
        edition = kwargs.pop('edition', 1)
        time_code = kwargs.pop('time_code', None)
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
        self.update({
            'Ni': 1,
            'Nj': 1,
            'numberOfValues': 1,
            'alternativeRowScanning': 0,
            'centre': 'ecmf',
            'year': 2007,
            'month': 3,
            'day': 23,
            'hour': 12,
            'minute': 0,
            'indicatorOfUnitOfTimeRange': 1,
            'shapeOfTheEarth': 6,
            'gridType': 'rotated_ll',
            'angleOfRotation': 0.0,
            'iDirectionIncrementInDegrees': 0.036,
            'jDirectionIncrementInDegrees': 0.036,
            'iScansNegatively': 0,
            'jScansPositively': 1,
            'longitudeOfFirstGridPointInDegrees': -5.70,
            'latitudeOfFirstGridPointInDegrees': -4.452,
            'jPointsAreConsecutive': 0,
            'values': np.array([[1.0]]),
            'indicatorOfParameter': 9999,
            'parameterNumber': 9999,
        })
        # Add edition-dependent settings.
        self['edition'] = edition
        if edition == 1:
            self.update({
                'startStep': 24,
                'timeRangeIndicator': 1,
                'P1': 2, 'P2': 0,
                # time unit - needed AS WELL as 'indicatorOfUnitOfTimeRange'
                'unitOfTime': 1,
                'table2Version': 9999,
            })
        if edition == 2:
            self.update({
                'iDirectionIncrementGiven': 1,
                'jDirectionIncrementGiven': 1,
                'uvRelativeToGrid': 0,
                'forecastTime': 24,
                'productDefinitionTemplateNumber': 0,
                'stepRange': 24,
                'discipline': 9999,
                'parameterCategory': 9999,
                'tablesVersion': 4
            })

    def set_timeunit_code(self, timecode):
        # Do timecode setting (somewhat edition-dependent).
        self['indicatorOfUnitOfTimeRange'] = timecode
        if self['edition'] == 1:
            # for some odd reason, GRIB1 code uses *both* of these
            # NOTE kludge -- the 2 keys are really the same thing
            self['unitOfTime'] = timecode


class TestGribTimecodes(tests.IrisGribTest):
    def _run_timetests(self, test_set):
        # Check the unit-handling for given units-codes and editions.

        # Operates on lists of cases for various time-units and grib-editions.
        # Format: (edition, code, expected-exception,
        #          equivalent-seconds, description-string)
        for test_controls in test_set:
            (
                grib_edition, timeunit_codenum,
                expected_error,
                timeunit_secs, timeunit_str
            ) = test_controls

            # Construct a suitable fake test message.
            message = FakeGribMessage(
                edition=grib_edition,
                time_code=timeunit_codenum
            )

            if expected_error:
                # Expect GribWrapper construction to fail.
                with self.assertRaises(type(expected_error)) as ar_context:
                    msg = GribWrapper(message)
                self.assertEqual(
                    ar_context.exception.args,
                    expected_error.args)
                continue

            # 'ELSE'...
            # Expect the wrapper construction to work.
            # Make a GribWrapper object and test it.
            wrapped_msg = GribWrapper(message)

            # Check the units string.
            forecast_timeunit = wrapped_msg._forecastTimeUnit
            self.assertEqual(
                forecast_timeunit, timeunit_str,
                'Bad unit string for edition={ed:01d}, '
                'unitcode={code:01d} : '
                'expected="{wanted}" GOT="{got}"'.format(
                    ed=grib_edition,
                    code=timeunit_codenum,
                    wanted=timeunit_str,
                    got=forecast_timeunit
                )
            )

            # Check the data-starttime calculation.
            interval_start_to_end = (wrapped_msg._phenomenonDateTime -
                                     wrapped_msg._referenceDateTime)
            if grib_edition == 1:
                interval_from_units = wrapped_msg.P1
            else:
                interval_from_units = wrapped_msg.forecastTime
            interval_from_units *= datetime.timedelta(0, timeunit_secs)
            self.assertEqual(
                interval_start_to_end, interval_from_units,
                'Inconsistent start time offset for edition={ed:01d}, '
                'unitcode={code:01d} : '
                'from-unit="{unit_str}" '
                'from-phenom-minus-ref="{e2e_str}"'.format(
                    ed=grib_edition,
                    code=timeunit_codenum,
                    unit_str=interval_from_units,
                    e2e_str=interval_start_to_end
                )
            )

    # Test groups of testcases for various time-units and grib-editions.
    # Format: (edition, code, expected-exception,
    #          equivalent-seconds, description-string)
    def test_timeunits_common(self):
        tests = (
            (1, 0, None, 60.0, 'minutes'),
            (1, 1, None, _hour_secs, 'hours'),
            (1, 2, None, 24.0 * _hour_secs, 'days'),
            (1, 10, None, 3.0 * _hour_secs, '3 hours'),
            (1, 11, None, 6.0 * _hour_secs, '6 hours'),
            (1, 12, None, 12.0 * _hour_secs, '12 hours'),
        )
        TestGribTimecodes._run_timetests(self, tests)

    @staticmethod
    def _err_bad_timeunit(code):
        return NotYetImplementedError(
            'Unhandled time unit for forecast '
            'indicatorOfUnitOfTimeRange : {code}'.format(code=code)
        )

    def test_timeunits_grib1_specific(self):
        tests = (
            (1, 13, None, 0.25 * _hour_secs, '15 minutes'),
            (1, 14, None, 0.5 * _hour_secs, '30 minutes'),
            (1, 254, None, 1.0, 'seconds'),
            (1, 111, TestGribTimecodes._err_bad_timeunit(111), 1.0, '??'),
        )
        TestGribTimecodes._run_timetests(self, tests)

    def test_timeunits_calendar(self):
        tests = (
            (1, 3, TestGribTimecodes._err_bad_timeunit(3), 0.0, 'months'),
            (1, 4, TestGribTimecodes._err_bad_timeunit(4), 0.0, 'years'),
            (1, 5, TestGribTimecodes._err_bad_timeunit(5), 0.0, 'decades'),
            (1, 6, TestGribTimecodes._err_bad_timeunit(6), 0.0, '30 years'),
            (1, 7, TestGribTimecodes._err_bad_timeunit(7), 0.0, 'centuries'),
        )
        TestGribTimecodes._run_timetests(self, tests)

    def test_timeunits_invalid(self):
        tests = (
            (1, 111, TestGribTimecodes._err_bad_timeunit(111), 1.0, '??'),
        )
        TestGribTimecodes._run_timetests(self, tests)

    def test_warn_unknown_pdts(self):
        # Test loading of an unrecognised GRIB Product Definition Template.

        # Get a temporary file by name (deleted afterward by context).
        with self.temp_filename() as temp_gribfile_path:
            # Write a test grib message to the temporary file.
            with open(temp_gribfile_path, 'wb') as temp_gribfile:
                grib_message = gribapi.grib_new_from_samples('GRIB2')
                # Set the PDT to something unexpected.
                gribapi.grib_set_long(
                    grib_message, 'productDefinitionTemplateNumber', 5)
                gribapi.grib_write(grib_message, temp_gribfile)

            # Load the message from the file as a cube.
            cube_generator = load_cubes(temp_gribfile_path)
            with self.assertRaises(TranslationError) as te:
                cube = next(cube_generator)
            self.assertEqual('Product definition template [5]'
                             ' is not supported', str(te.exception))


if __name__ == "__main__":
    tests.main()
