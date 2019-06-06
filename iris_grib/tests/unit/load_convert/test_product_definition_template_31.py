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
Tests for `iris_grib._load_convert.product_definition_template_31`.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from copy import deepcopy
import mock
import numpy as np
import warnings

from iris.coords import AuxCoord
from iris_grib.tests.unit.load_convert import empty_metadata

from iris_grib._load_convert import product_definition_template_31


def section_4():
    # also needed for test_product_definition_section.py
    series = mock.sentinel.satelliteSeries
    number = mock.sentinel.satelliteNumber
    instrument = mock.sentinel.instrumentType
    return {'NB': 1,
            'satelliteSeries': series,
            'satelliteNumber': number,
            'instrumentType': instrument,
            'scaleFactorOfCentralWaveNumber': 1,
            'scaledValueOfCentralWaveNumber': 12}


class Test(tests.IrisGribTest):
    def setUp(self):
        self.patch('warnings.warn')
        self.satellite_common_patch = self.patch(
            'iris_grib._load_convert.satellite_common')
        self.generating_process_patch = self.patch(
            'iris_grib._load_convert.generating_process')

    def test(self):
        # Prepare the arguments.
        rt_coord = mock.sentinel.observation_time
        section = section_4()

        # Call the function.
        metadata = empty_metadata()
        product_definition_template_31(section, metadata, rt_coord)

        # Check that 'satellite_common' was called.
        self.assertEqual(self.satellite_common_patch.call_count, 1)
        # Check that 'generating_process' was called.
        self.assertEqual(self.generating_process_patch.call_count, 1)
        # Check that the scalar time coord was added in.
        self.assertIn((rt_coord, None), metadata['aux_coords_and_dims'])


if __name__ == '__main__':
    tests.main()
