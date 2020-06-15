# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for
:func:`iris_grib._load_convert.grid_definition_template_140`.
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

from iris_grib._load_convert import grid_definition_template_140


class Test(tests.IrisGribTest):

    def section_3(self):
        section = {
            'gridDefinitionTemplateNumber': 140,
            'shapeOfTheEarth': 4,
            'scaleFactorOfRadiusOfSphericalEarth': MDI,
            'scaledValueOfRadiusOfSphericalEarth': MDI,
            'scaleFactorOfEarthMajorAxis': MDI,
            'scaledValueOfEarthMajorAxis': MDI,
            'scaleFactorOfEarthMinorAxis': MDI,
            'scaledValueOfEarthMinorAxis': MDI,
            'numberOfPointsAlongXAxis': 2,
            'numberOfPointsAlongYAxis': 2,
            'latitudeOfFirstGridPoint': 53988880,
            'longitudeOfFirstGridPoint': -4027984,
            'standardParallelInMicrodegrees': 54900000,
            'centralLongitudeInMicrodegrees': -2500000,
            'resolutionAndComponentFlags': 0b00110000,
            'xDirectionGridLengthInMillimetres': 2000000,
            'yDirectionGridLengthInMillimetres': 2000000,
            'scanningMode': 0b01000000,
        }
        return section

    def expected(self, y_dim, x_dim):
        # Prepare the expectation.
        expected = empty_metadata()
        ellipsoid = iris.coord_systems.GeogCS(
            6378137,
            inverse_flattening=298.257222101)
        cs = iris.coord_systems.LambertAzimuthalEqualArea(
            latitude_of_projection_origin=54.9,
            longitude_of_projection_origin=-2.5,
            false_easting=0,
            false_northing=0,
            ellipsoid=ellipsoid)
        lon0 = -4027984 * 1e-6
        lat0 = 53988880 * 1e-6
        x0m, y0m = cs.as_cartopy_crs().transform_point(
            lon0, lat0, ccrs.Geodetic())
        dxm = dym = 2000.
        x_points = x0m + dxm * np.arange(2)
        y_points = y0m + dym * np.arange(2)
        x = iris.coords.DimCoord(x_points,
                                 standard_name='projection_x_coordinate',
                                 units='m',
                                 coord_system=cs)
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
        grid_definition_template_140(section, metadata)
        expected = self.expected(0, 1)
        self.assertEqual(metadata, expected)


if __name__ == '__main__':
    tests.main()
