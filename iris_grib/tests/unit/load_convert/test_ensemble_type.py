# (C) British Crown Copyright 2016, Met Office
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
"""
Test function
:func:`iris_grib._load_convert.ensemble_type`.

"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.exceptions import TranslationError
from iris_grib._load_convert import ensemble_type
from iris_grib._load_convert import _MDI
from iris_grib.tests.unit.load_convert import empty_metadata


class Test(tests.IrisGribTest):
    def setUp(self):
        # Create a dictionary representing a sample section 4 from a grib file.
        self.section = {'productDefinitionTemplateNumber': 15,
            'hoursAfterDataCutoff': _MDI,
            'minutesAfterDataCutoff': _MDI,
            'indicatorOfUnitOfTimeRange': 0,  # minutes
            'forecastTime': 360,
            'NV': 0,
            'typeOfFirstFixedSurface': 103,
            'scaleFactorOfFirstFixedSurface': 0,
            'scaledValueOfFirstFixedSurface': 9999,
            'typeOfSecondFixedSurface': 255,
            }
        self.metadata = empty_metadata()

    def test_type_0(self):
        # Grab clean section 4 sample and metadata, apply code
        section = self.section
        section['typeOfEnsembleForecast'] = 0
        metadata = self.metadata

        # Obtain ensemble type and add it to metadata
        ensemble_type(section, metadata)
        self.assertEqual(metadata[ensemble_type],
                         'Unperturbed high-resolution control forecast')

    def test_type_1(self):
        # Grab clean section 4 sample and metadata, apply code
        section = self.section
        section['typeOfEnsembleForecast'] = 1
        metadata = self.metadata

        # Obtain ensemble type and add it to metadata, apply code
        ensemble_type(section, metadata)
        self.assertEqual(metadata[ensemble_type],
                         'Unperturbed low resolution control forecast')

    def test_type_2(self):
        # Grab clean section 4 sample and metadata, apply code
        section = self.section
        section['typeOfEnsembleForecast'] = 2
        metadata = self.metadata

        # Obtain ensemble type and add it to metadata, apply code
        ensemble_type(section, metadata)
        self.assertEqual(metadata[ensemble_type],
                         'Negatively perturbed forecast')

    def test_type_3(self):
        # Grab clean section 4 sample and metadata, apply code
        section = self.section
        section['typeOfEnsembleForecast'] = 3
        metadata = self.metadata

        # Obtain ensemble type and add it to metadata, apply code
        ensemble_type(section, metadata)
        self.assertEqual(metadata[ensemble_type],
                         'Positively perturbed forecast')

    def test_type_4(self):
        # Grab clean section 4 sample and metadata, apply code
        section = self.section
        section['typeOfEnsembleForecast'] = 4
        metadata = self.metadata

        # Obtain ensemble type and add it to metadata, apply code
        ensemble_type(section, metadata)
        self.assertEqual(metadata[ensemble_type],
                         'Multimodel forecast')

    def test_missing_type(self):
        # Grab clean section 4 sample and metadata, apply code
        section = self.section
        section['typeOfEnsembleForecast'] = _MDI
        metadata = self.metadata

        # Obtain ensemble type and add it to metadata
        msg = 'Product definition section 4 contains missing type of ' \
              'ensemble forecast.'
        with self.assertRaisesRegexp(TranslationError, msg):
            ensemble_type(section, metadata)

    def test_bad_type(self):
        # Grab clean section 4 sample and metadata
        section = self.section
        # Apply invalid code
        section['typeOfEnsembleForecast'] = 100
        metadata = self.metadata

        # Obtain ensemble type and add it to metadata
        msg = 'Product definition section 4 contains an unsupported ' \
              'ensemble forecast type [100]'
        with self.assertRaisesRegexp(TranslationError, msg):
            ensemble_type(section, metadata)


if __name__ == '__main__':
    tests.main()
