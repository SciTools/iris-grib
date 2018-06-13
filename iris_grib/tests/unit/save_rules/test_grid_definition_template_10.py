# (C) British Crown Copyright 2018, Met Office
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
Unit tests for :meth:`iris_grib._save_rules.grid_definition_template_10`.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import numpy as np

import iris.coords
from iris.coord_systems import GeogCS, Mercator

from iris_grib._save_rules import grid_definition_template_10
from iris_grib.tests.unit.save_rules import GdtTestMixin


class Test(tests.IrisGribTest, GdtTestMixin):
    def setUp(self):
        self.default_ellipsoid = GeogCS(semi_major_axis=6371200.0)
        self.mercator_test_cube = self._make_test_cube(coord_units='m')

        GdtTestMixin.setUp(self)

    def _default_coord_system(self):
        return Mercator(standard_parallel=14.,
                        ellipsoid=self.default_ellipsoid)

    def test__template_number(self):
        grid_definition_template_10(self.mercator_test_cube, self.mock_grib)
        self._check_key('gridDefinitionTemplateNumber', 10)

    def test__shape_of_earth(self):
        grid_definition_template_10(self.mercator_test_cube, self.mock_grib)
        self._check_key('shapeOfTheEarth', 1)
        self._check_key('scaleFactorOfRadiusOfSphericalEarth', 0)
        self._check_key('scaleFactorOfEarthMajorAxis', 0)
        self._check_key('scaledValueOfEarthMajorAxis', 0)
        self._check_key('scaleFactorOfEarthMinorAxis', 0)
        self._check_key('scaledValueOfEarthMinorAxis', 0)

    def test__grid_shape(self):
        n_x_points = 13
        n_y_points = 6
        test_cube = self._make_test_cube(x_points=np.arange(n_x_points),
                                         y_points=np.arange(n_y_points),
                                         coord_units='m')
        grid_definition_template_10(test_cube, self.mock_grib)
        self._check_key('Ni', n_x_points)
        self._check_key('Nj', n_y_points)

    def test__grid_points(self):
        test_cube = self._make_test_cube(x_points=[1e6, 3e6, 5e6, 7e6],
                                         y_points=[4e6, 9e6],
                                         coord_units='m')
        grid_definition_template_10(test_cube, self.mock_grib)
        self._check_key("latitudeOfFirstGridPoint", 34727738)
        self._check_key("longitudeOfFirstGridPoint", 9268240)
        self._check_key("latitudeOfLastGridPoint", 63746266)
        self._check_key("longitudeOfLastGridPoint", 64877681)
        self._check_key("Di", 2e9)
        self._check_key("Dj", 5e9)

    def test__template_specifics(self):
        grid_definition_template_10(self.mercator_test_cube, self.mock_grib)
        self._check_key("LaD", 14e6)

    def test__scanmode(self):
        grid_definition_template_10(self.mercator_test_cube, self.mock_grib)
        self._check_key('iScansPositively', 1)
        self._check_key('jScansPositively', 1)

    def test__scanmode_reverse(self):
        test_cube = self._make_test_cube(x_points=np.arange(7e6, 0, -1e6),
                                         coord_units='m')
        grid_definition_template_10(test_cube, self.mock_grib)
        self._check_key('iScansPositively', 0)
        self._check_key('jScansPositively', 1)


if __name__ == "__main__":
    tests.main()
