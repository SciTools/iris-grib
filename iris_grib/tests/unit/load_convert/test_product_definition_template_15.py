# (C) British Crown Copyright 2014 - 2017, Met Office
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
:func:`iris_grib._load_convert.product_definition_template_15`.

This basically copies code from 'test_product_definition_template_0', and adds
testing for the statistical method and spatial-processing type.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import mock

import iris.coords
from iris.exceptions import TranslationError
from iris.coords import CellMethod, DimCoord

import iris_grib
from iris_grib.tests.unit.load_convert import empty_metadata
from iris_grib.tests.unit.load_convert import LoadConvertTest
from iris_grib._load_convert import _MDI as MDI

from iris_grib._load_convert import product_definition_template_15


def section_4_sample():
    # Create a dictionary representing a sample section 4 from a grib file.
    return {'productDefinitionTemplateNumber': 15,
            'hoursAfterDataCutoff': MDI,
            'minutesAfterDataCutoff': MDI,
            'indicatorOfUnitOfTimeRange': 0,  # minutes
            'forecastTime': 360,
            'NV': 0,
            'typeOfFirstFixedSurface': 103,
            'scaleFactorOfFirstFixedSurface': 0,
            'scaledValueOfFirstFixedSurface': 9999,
            'typeOfSecondFixedSurface': 255,
            'statisticalProcess': 2,  # method = maximum
            'spatialProcessing': 0,  # from source grid, no interpolation
            'numberOfPointsUsed': 0  # unused?
            }


class Test(LoadConvertTest):
    def setUp(self):
        self.time_coord = DimCoord(24, 'time', units='hours since epoch')
        self.forecast_period_coord = DimCoord(6, 'forecast_period',
                                              units='hours')
        self.forecast_ref_time_coord = DimCoord(18, 'forecast_reference_time',
                                                units='hours since epoch')
        self.height_coord = iris.coords.DimCoord(9999, long_name='height',
                                                 units='m')

    def _translate(self, section):
        # Use pdt 15 to populate a metadata dict from the section 4 keys
        metadata = empty_metadata()
        product_definition_template_15(section, metadata,
                                       self.time_coord)
        return metadata

    def test_time_coord(self):
        # Generate metadata from running our sample section through pdt 15.
        metadata = self._translate(section_4_sample())

        # Generate a fresh metadata dict and manually populate it with metadata
        # that we expect will be generated from our sample section.
        expected = empty_metadata()
        aux = expected['aux_coords_and_dims']
        aux.append((self.forecast_period_coord, None))
        aux.append((self.forecast_ref_time_coord, None))
        aux.append((self.time_coord, None))
        aux.append((self.height_coord, None))

        expected['cell_methods'] = [CellMethod(coords=('area',),
                                               method='maximum')]

        # Now check that the section conversion produces the metadata we
        # expect.
        self.assertMetadataEqual(metadata, expected)

    def test_bad_statistic_method(self):
        section = section_4_sample()
        section['statisticalProcess'] = 999
        msg = ('unsupported statistical process type \[999\]')
        with self.assertRaisesRegexp(TranslationError, msg):
            self._translate(section)

    def test_bad_spatial_processing_code(self):
        section = section_4_sample()
        section['spatialProcessing'] = 999
        msg = ('unsupported spatial processing type \[999\]')
        with self.assertRaisesRegexp(TranslationError, msg):
            self._translate(section)


if __name__ == '__main__':
    tests.main()
