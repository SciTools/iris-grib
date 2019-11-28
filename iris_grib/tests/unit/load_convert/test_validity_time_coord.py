# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.validity_time_coord.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock

from cf_units import Unit
from iris.coords import DimCoord
import numpy as np

from iris_grib._load_convert import validity_time_coord


class Test(tests.IrisGribTest):
    def setUp(self):
        self.fp = DimCoord(5, standard_name='forecast_period', units='hours')
        self.fp_test_bounds = np.array([[1.0, 9.0]])
        self.unit = Unit('hours since epoch')
        self.frt = DimCoord(10, standard_name='forecast_reference_time',
                            units=self.unit)

    def test_frt_shape(self):
        frt = mock.Mock(shape=(2,))
        fp = mock.Mock(shape=(1,))
        emsg = 'scalar forecast reference time'
        with self.assertRaisesRegex(ValueError, emsg):
            validity_time_coord(frt, fp)

    def test_fp_shape(self):
        frt = mock.Mock(shape=(1,))
        fp = mock.Mock(shape=(2,))
        emsg = 'scalar forecast period'
        with self.assertRaisesRegex(ValueError, emsg):
            validity_time_coord(frt, fp)

    def test(self):
        coord = validity_time_coord(self.frt, self.fp)
        self.assertIsInstance(coord, DimCoord)
        self.assertEqual(coord.standard_name, 'time')
        self.assertEqual(coord.units, self.unit)
        self.assertEqual(coord.shape, (1,))
        point = self.frt.points[0] + self.fp.points[0]
        self.assertEqual(coord.points[0], point)
        self.assertFalse(coord.has_bounds())

    def test_bounded(self):
        self.fp.bounds = self.fp_test_bounds
        coord = validity_time_coord(self.frt, self.fp)
        self.assertIsInstance(coord, DimCoord)
        self.assertEqual(coord.standard_name, 'time')
        self.assertEqual(coord.units, self.unit)
        self.assertEqual(coord.shape, (1,))
        point = self.frt.points[0] + self.fp.points[0]
        self.assertEqual(coord.points[0], point)
        self.assertTrue(coord.has_bounds())
        bounds = self.frt.points[0] + self.fp_test_bounds
        self.assertArrayAlmostEqual(coord.bounds, bounds)


if __name__ == '__main__':
    tests.main()
