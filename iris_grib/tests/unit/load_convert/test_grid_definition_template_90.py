# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for
:func:`iris_grib._load_convert.grid_definition_template_90`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import numpy as np

import iris.coord_systems
import iris.coords
import iris.exceptions

from iris_grib.tests.unit.load_convert import empty_metadata
from iris_grib._load_convert import _MDI as MDI

from iris_grib._load_convert import grid_definition_template_90


class Test(tests.IrisGribTest):
    def uk(self):
        section = {
            'shapeOfTheEarth': 3,
            'scaleFactorOfRadiusOfSphericalEarth': MDI,
            'scaledValueOfRadiusOfSphericalEarth': MDI,
            'scaleFactorOfEarthMajorAxis': 4,
            'scaledValueOfEarthMajorAxis': 63781688,
            'scaleFactorOfEarthMinorAxis': 4,
            'scaledValueOfEarthMinorAxis': 63565840,
            'Nx': 390,
            'Ny': 227,
            'latitudeOfSubSatellitePoint': 0,
            'longitudeOfSubSatellitePoint': 0,
            'resolutionAndComponentFlags': 0,
            'dx': 3622,
            'dy': 3610,
            'Xp': 1856000,
            'Yp': 1856000,
            'scanningMode': 192,
            'orientationOfTheGrid': 0,
            'Nr': 6610674,
            'Xo': 1733,
            'Yo': 3320
        }
        return section

    def expected_uk(self, y_dim, x_dim):
        # Prepare the expectation.
        expected = empty_metadata()
        major = 6378168.8
        ellipsoid = iris.coord_systems.GeogCS(major, 6356584.0)
        height = (6610674e-6 - 1) * major
        lat = lon = 0
        easting = northing = 0
        cs = iris.coord_systems.Geostationary(
            latitude_of_projection_origin=lat,
            longitude_of_projection_origin=lon,
            perspective_point_height=height,
            sweep_angle_axis='y',
            false_easting=easting,
            false_northing=northing,
            ellipsoid=ellipsoid)
        nx = 390
        x_origin = 0.010313624253429191
        dx = -8.38506036864162e-05
        x = iris.coords.DimCoord(np.arange(nx) * dx + x_origin,
                                 'projection_x_coordinate', units='radians',
                                 coord_system=cs)
        ny = 227
        y_origin = 0.12275487535118533
        dy = 8.384895857321404e-05
        y = iris.coords.DimCoord(np.arange(ny) * dy + y_origin,
                                 'projection_y_coordinate', units='radians',
                                 coord_system=cs)
        expected['dim_coords_and_dims'].append((y, y_dim))
        expected['dim_coords_and_dims'].append((x, x_dim))
        return expected

    def compare(self, metadata, expected):
        # Compare the result with the expectation.
        self.assertEqual(len(metadata['dim_coords_and_dims']),
                         len(expected['dim_coords_and_dims']))
        for result_pair, expected_pair in zip(metadata['dim_coords_and_dims'],
                                              expected['dim_coords_and_dims']):
            result_coord, result_dims = result_pair
            expected_coord, expected_dims = expected_pair
            # Take copies for safety, as we are going to modify them.
            result_coord, expected_coord = [co.copy() for co in
                                            (result_coord, expected_coord)]
            # Ensure the dims match.
            self.assertEqual(result_dims, expected_dims)
            # Ensure the coordinate systems match (allowing for precision).
            result_cs = result_coord.coord_system
            expected_cs = expected_coord.coord_system
            self.assertEqual(type(result_cs), type(expected_cs))
            self.assertEqual(result_cs.latitude_of_projection_origin,
                             expected_cs.latitude_of_projection_origin)
            self.assertEqual(result_cs.longitude_of_projection_origin,
                             expected_cs.longitude_of_projection_origin)
            self.assertAlmostEqual(result_cs.perspective_point_height,
                                   expected_cs.perspective_point_height)
            self.assertEqual(result_cs.false_easting,
                             expected_cs.false_easting)
            self.assertEqual(result_cs.false_northing,
                             expected_cs.false_northing)
            self.assertAlmostEqual(result_cs.ellipsoid.semi_major_axis,
                                   expected_cs.ellipsoid.semi_major_axis)
            self.assertEqual(result_cs.ellipsoid.semi_minor_axis,
                             expected_cs.ellipsoid.semi_minor_axis)
            # Now we can ignore the coordinate systems and compare the
            # rest of the coordinate attributes.
            result_coord.coord_system = None
            expected_coord.coord_system = None

            # Likewise, first compare the points (and optional bounds)
            # *approximately*, then force those equal + compare other aspects.
            self.assertArrayAlmostEqual(result_coord.points,
                                        expected_coord.points)
            result_coord.points = expected_coord.points
            if result_coord.has_bounds() and expected_coord.has_bounds():
                self.assertArrayAlmostEqual(result_coord.bounds,
                                            expected_coord.bounds)
                result_coord.bounds = expected_coord.bounds

            # Compare the coords, having equalised the array values.
            self.assertEqual(result_coord, expected_coord)

        # Ensure no other metadata was created.
        for name in expected.keys():
            if name == 'dim_coords_and_dims':
                continue
            self.assertEqual(metadata[name], expected[name])

    def test_uk(self):
        section = self.uk()
        metadata = empty_metadata()
        grid_definition_template_90(section, metadata)
        expected = self.expected_uk(0, 1)
        self.compare(metadata, expected)

    def test_uk_transposed(self):
        section = self.uk()
        section['scanningMode'] = 0b11100000
        metadata = empty_metadata()
        grid_definition_template_90(section, metadata)
        expected = self.expected_uk(1, 0)
        self.compare(metadata, expected)

    def test_non_zero_latitude(self):
        section = self.uk()
        section['latitudeOfSubSatellitePoint'] = 1
        metadata = empty_metadata()
        with self.assertRaisesRegex(iris.exceptions.TranslationError,
                                    'non-zero latitude'):
            grid_definition_template_90(section, metadata)

    def test_rotated_meridian(self):
        section = self.uk()
        section['orientationOfTheGrid'] = 1
        metadata = empty_metadata()
        with self.assertRaisesRegex(iris.exceptions.TranslationError,
                                    'orientation'):
            grid_definition_template_90(section, metadata)

    def test_zero_height(self):
        section = self.uk()
        section['Nr'] = 0
        metadata = empty_metadata()
        with self.assertRaisesRegex(iris.exceptions.TranslationError,
                                    'zero'):
            grid_definition_template_90(section, metadata)

    def test_orthographic(self):
        section = self.uk()
        section['Nr'] = MDI
        metadata = empty_metadata()
        with self.assertRaisesRegex(iris.exceptions.TranslationError,
                                    'orthographic'):
            grid_definition_template_90(section, metadata)

    def test_scanning_mode_positive_x(self):
        section = self.uk()
        section['scanningMode'] = 0b01000000
        metadata = empty_metadata()
        with self.assertRaisesRegex(iris.exceptions.TranslationError, r'\+x'):
            grid_definition_template_90(section, metadata)

    def test_scanning_mode_negative_y(self):
        section = self.uk()
        section['scanningMode'] = 0b10000000
        metadata = empty_metadata()
        with self.assertRaisesRegex(iris.exceptions.TranslationError, '-y'):
            grid_definition_template_90(section, metadata)


if __name__ == '__main__':
    tests.main()
