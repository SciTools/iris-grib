# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function
:func:`iris_grib._load_convert.grid_definition_template_0_and_1`.

"""

# Import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import numpy as np

import iris.coord_systems
import iris.coords

from iris.exceptions import TranslationError

from iris_grib.tests.unit.load_convert import empty_metadata

from iris_grib._load_convert import grid_definition_template_0_and_1


class _Section(dict):
    def get_computed_key(self, key):
        return self.get(key)


class Test_resolution_flags(tests.IrisGribTest):

    def section_3(self):
        section = _Section({
            'Ni': 6,
            'Nj': 6,
            'latitudeOfFirstGridPoint': 0,
            'longitudeOfFirstGridPoint': 0,
            'resolutionAndComponentFlags': 0,
            'latitudeOfLastGridPoint': 5000000,
            'longitudeOfLastGridPoint': 5000000,
            'iDirectionIncrement': 0,
            'jDirectionIncrement': 0,
            'scanningMode': 0b01000000,
            'numberOfOctectsForNumberOfPoints': 0,
            'interpretationOfNumberOfPoints': 0,
        })
        return section

    def expected(self, x_dim, y_dim, x_points, y_points, x_neg=True,
                 y_neg=True):
        # Prepare the expectation.
        expected = empty_metadata()
        cs = iris.coord_systems.GeogCS(6367470)
        if x_neg:
            x_points = x_points[::-1]
        x = iris.coords.DimCoord(x_points,
                                 standard_name='longitude',
                                 units='degrees',
                                 coord_system=cs)
        if y_neg:
            y_points = y_points[::-1]
        y = iris.coords.DimCoord(y_points,
                                 standard_name='latitude',
                                 units='degrees',
                                 coord_system=cs)
        expected['dim_coords_and_dims'].append((y, y_dim))
        expected['dim_coords_and_dims'].append((x, x_dim))
        return expected

    def test_without_increments(self):
        section = self.section_3()
        metadata = empty_metadata()
        cs = iris.coord_systems.GeogCS(6367470)
        grid_definition_template_0_and_1(section, metadata, 'latitude',
                                         'longitude', cs)
        x_points = np.array([0., 1., 2., 3., 4., 5.])
        y_points = np.array([0., 1., 2., 3., 4., 5.])
        expected = self.expected(1, 0, x_points, y_points, x_neg=False,
                                 y_neg=False)
        self.assertEqual(metadata, expected)

    def test_with_increments(self):
        section = self.section_3()
        section['resolutionAndComponentFlags'] = 48
        section['iDirectionIncrement'] = 1000000
        section['jDirectionIncrement'] = 1000000
        metadata = empty_metadata()
        cs = iris.coord_systems.GeogCS(6367470)
        grid_definition_template_0_and_1(section, metadata, 'latitude',
                                         'longitude', cs)
        x_points = np.array([0., 1., 2., 3., 4., 5.])
        y_points = np.array([0., 1., 2., 3., 4., 5.])
        expected = self.expected(1, 0, x_points, y_points, x_neg=False,
                                 y_neg=False)
        self.assertEqual(metadata, expected)

    def test_with_i_not_j_increment(self):
        section = self.section_3()
        section['resolutionAndComponentFlags'] = 32
        section['iDirectionIncrement'] = 1000000
        metadata = empty_metadata()
        cs = iris.coord_systems.GeogCS(6367470)
        grid_definition_template_0_and_1(section, metadata, 'latitude',
                                         'longitude', cs)
        x_points = np.array([0., 1., 2., 3., 4., 5.])
        y_points = np.array([0., 1., 2., 3., 4., 5.])
        expected = self.expected(1, 0, x_points, y_points, x_neg=False,
                                 y_neg=False)
        self.assertEqual(metadata, expected)

    def test_with_j_not_i_increment(self):
        section = self.section_3()
        section['resolutionAndComponentFlags'] = 16
        section['jDirectionIncrement'] = 1000000
        metadata = empty_metadata()
        cs = iris.coord_systems.GeogCS(6367470)
        grid_definition_template_0_and_1(section, metadata, 'latitude',
                                         'longitude', cs)
        x_points = np.array([0., 1., 2., 3., 4., 5.])
        y_points = np.array([0., 1., 2., 3., 4., 5.])
        expected = self.expected(1, 0, x_points, y_points, x_neg=False,
                                 y_neg=False)
        self.assertEqual(metadata, expected)

    def test_without_increments_crossing_0_lon(self):
        section = self.section_3()
        section['longitudeOfFirstGridPoint'] = 355000000
        section['Ni'] = 11
        metadata = empty_metadata()
        cs = iris.coord_systems.GeogCS(6367470)
        grid_definition_template_0_and_1(section, metadata, 'latitude',
                                         'longitude', cs)
        x_points = np.array(
            [355., 356., 357., 358., 359., 360., 361., 362., 363., 364., 365.]
        )
        y_points = np.array([0., 1., 2., 3., 4., 5.])
        expected = self.expected(1, 0, x_points, y_points, x_neg=False,
                                 y_neg=False)
        self.assertEqual(metadata, expected)


class Test(tests.IrisGribTest):

    def test_unsupported_quasi_regular__number_of_octets(self):
        section = {'numberOfOctectsForNumberOfPoints': 1}
        cs = None
        metadata = None
        with self.assertRaisesRegex(TranslationError, 'quasi-regular'):
            grid_definition_template_0_and_1(section,
                                             metadata,
                                             'latitude',
                                             'longitude',
                                             cs)

    def test_unsupported_quasi_regular__interpretation(self):
        section = {'numberOfOctectsForNumberOfPoints': 1,
                   'interpretationOfNumberOfPoints': 1}
        cs = None
        metadata = None
        with self.assertRaisesRegex(TranslationError, 'quasi-regular'):
            grid_definition_template_0_and_1(section,
                                             metadata,
                                             'latitude',
                                             'longitude',
                                             cs)


if __name__ == '__main__':
    tests.main()
