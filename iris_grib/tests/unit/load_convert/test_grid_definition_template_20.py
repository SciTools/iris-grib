# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for
:func:`iris_grib._load_convert.grid_definition_template_20`.
"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import cartopy.crs as ccrs
import numpy as np

import iris.coord_systems
import iris.coords

from iris_grib.tests.unit.load_convert import empty_metadata
from iris_grib._load_convert import _MDI as MDI

from iris_grib._load_convert import grid_definition_template_20


class Test(tests.IrisGribTest):

    def section_3(self):
        section = {
            'gridDefinitionTemplateNumber': 20,
            'shapeOfTheEarth': 0,
            'scaleFactorOfRadiusOfSphericalEarth': 0,
            'scaledValueOfRadiusOfSphericalEarth': 6367470,
            'scaleFactorOfEarthMajorAxis': 0,
            'scaledValueOfEarthMajorAxis': MDI,
            'scaleFactorOfEarthMinorAxis': 0,
            'scaledValueOfEarthMinorAxis': MDI,
            'Nx': 15,
            'Ny': 10,
            'latitudeOfFirstGridPoint': 32549114,
            'longitudeOfFirstGridPoint': 225385728,
            'resolutionAndComponentFlags': 0b00001000,
            'LaD': 60000000,
            'orientationOfTheGrid': 262000000,
            'Dx': 320000000,
            'Dy': 320000000,
            'projectionCentreFlag': 0b00000000,
            'scanningMode': 0b01000000,
        }
        return section

    def expected(self, y_dim, x_dim):
        # Prepare the expectation.
        expected = empty_metadata()
        ellipsoid = iris.coord_systems.GeogCS(6367470)
        cs = iris.coord_systems.Stereographic(central_lat=90.,
                                              central_lon=262.,
                                              false_easting=0,
                                              false_northing=0,
                                              true_scale_lat=60.,
                                              ellipsoid=ellipsoid)
        lon0 = 225385728 * 1e-6
        lat0 = 32549114 * 1e-6
        x0m, y0m = cs.as_cartopy_crs().transform_point(
            lon0, lat0, ccrs.Geodetic())
        dxm = dym = 320000.
        x_points = x0m + dxm * np.arange(15)
        y_points = y0m + dym * np.arange(10)
        x = iris.coords.DimCoord(x_points,
                                 standard_name='projection_x_coordinate',
                                 units='m',
                                 coord_system=cs,
                                 circular=False)
        y = iris.coords.DimCoord(y_points,
                                 standard_name='projection_y_coordinate',
                                 units='m',
                                 coord_system=cs)
        expected['dim_coords_and_dims'].append((y, y_dim))
        expected['dim_coords_and_dims'].append((x, x_dim))
        return expected

    def test(self):
        section = self.section_3()
        metadata = empty_metadata()
        grid_definition_template_20(section, metadata)
        expected = self.expected(0, 1)
        self.assertEqual(metadata, expected)


if __name__ == '__main__':
    tests.main()
