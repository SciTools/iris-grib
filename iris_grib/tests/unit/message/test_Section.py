# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for `iris_grib.message.Section`.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

import gribapi
import numpy as np

from iris_grib.message import Section


@tests.skip_data
class Test___getitem__(tests.IrisGribTest):
    def setUp(self):
        filename = tests.get_data_path(('GRIB', 'uk_t', 'uk_t.grib2'))
        with open(filename, 'rb') as grib_fh:
            self.grib_id = gribapi.grib_new_from_file(grib_fh)

    def test_scalar(self):
        section = Section(self.grib_id, None, ['Ni'])
        self.assertEqual(section['Ni'], 47)

    def test_array(self):
        section = Section(self.grib_id, None, ['codedValues'])
        codedValues = section['codedValues']
        self.assertEqual(codedValues.shape, (1551,))
        self.assertArrayAlmostEqual(codedValues[:3],
                                    [-1.78140259, -1.53140259, -1.28140259])

    def test_typeOfFirstFixedSurface(self):
        section = Section(self.grib_id, None, ['typeOfFirstFixedSurface'])
        self.assertEqual(section['typeOfFirstFixedSurface'], 100)

    def test_numberOfSection(self):
        n = 4
        section = Section(self.grib_id, n, ['numberOfSection'])
        self.assertEqual(section['numberOfSection'], n)

    def test_invalid(self):
        section = Section(self.grib_id, None, ['Ni'])
        with self.assertRaisesRegex(KeyError, 'Nii'):
            section['Nii']


@tests.skip_data
class Test__getitem___pdt_31(tests.IrisGribTest):
    def setUp(self):
        filename = tests.get_data_path(('GRIB', 'umukv', 'ukv_chan9.grib2'))
        with open(filename, 'rb') as grib_fh:
            self.grib_id = gribapi.grib_new_from_file(grib_fh)
        self.keys = ['satelliteSeries', 'satelliteNumber', 'instrumentType',
                     'scaleFactorOfCentralWaveNumber',
                     'scaledValueOfCentralWaveNumber']

    def test_array(self):
        section = Section(self.grib_id, None, self.keys)
        for key in self.keys:
            value = section[key]
            self.assertIsInstance(value, np.ndarray)
            self.assertEqual(value.shape, (1,))


@tests.skip_data
class Test_get_computed_key(tests.IrisGribTest):
    def test_gdt40_computed(self):
        fname = tests.get_data_path(('GRIB', 'gaussian', 'regular_gg.grib2'))
        with open(fname, 'rb') as grib_fh:
            self.grib_id = gribapi.grib_new_from_file(grib_fh)
            section = Section(self.grib_id, None, [])
        latitudes = section.get_computed_key('latitudes')
        self.assertTrue(88.55 < latitudes[0] < 88.59)


if __name__ == '__main__':
    tests.main()
