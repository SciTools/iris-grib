# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for
:func:`iris_grib._load_convert.grid_definition_template_10`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import numpy as np

import iris.coord_systems
import iris.coords
import iris.exceptions

from iris_grib.tests.unit.load_convert import empty_metadata

from iris_grib._load_convert import grid_definition_template_10


class Test(tests.IrisGribTest):
    def section_3(self):
        section = {
            'gridDefinitionTemplateNumber': 10,
            'shapeOfTheEarth': 1,
            'scaleFactorOfRadiusOfSphericalEarth': 0,
            'scaledValueOfRadiusOfSphericalEarth': 6371200,
            'scaleFactorOfEarthMajorAxis': 0,
            'scaledValueOfEarthMajorAxis': 0,
            'scaleFactorOfEarthMinorAxis': 0,
            'scaledValueOfEarthMinorAxis': 0,
            'Ni': 181,
            'Nj': 213,
            'latitudeOfFirstGridPoint': 2351555,
            'latitudeOfLastGridPoint': 25088204,
            'LaD': 14000000,
            'longitudeOfFirstGridPoint': 114990304,
            'longitudeOfLastGridPoint': 135009712,
            'resolutionAndComponentFlags': 56,
            'scanningMode': 64,
            'Di': 12000000,
            'Dj': 12000000
        }
        return section

    def expected(self, y_dim, x_dim):
        # Prepare the expectation.
        expected = empty_metadata()
        ellipsoid = iris.coord_systems.GeogCS(6371200.0)
        cs = iris.coord_systems.Mercator(standard_parallel=14.,
                                         ellipsoid=ellipsoid)
        nx = 181
        x_origin = 12406918.990644248
        dx = 12000
        x = iris.coords.DimCoord(np.arange(nx) * dx + x_origin,
                                 'projection_x_coordinate',
                                 units='m',
                                 coord_system=cs)
        ny = 213
        y_origin = 253793.10903714459

        dy = 12000
        y = iris.coords.DimCoord(np.arange(ny) * dy + y_origin,
                                 'projection_y_coordinate',
                                 units='m',
                                 coord_system=cs)
        expected['dim_coords_and_dims'].append((y, y_dim))
        expected['dim_coords_and_dims'].append((x, x_dim))
        return expected

    def test(self):
        section = self.section_3()
        metadata = empty_metadata()
        grid_definition_template_10(section, metadata)
        expected = self.expected(y_dim=0, x_dim=1)
        self.assertEqual(metadata, expected)


if __name__ == '__main__':
    tests.main()
