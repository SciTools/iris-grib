# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.ellipsoid.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import numpy.ma as ma

import iris.coord_systems as icoord_systems
from iris.exceptions import TranslationError

from iris_grib._load_convert import ellipsoid


# Reference GRIB2 Code Table 3.2 - Shape of the Earth.


MDI = ma.masked


class Test(tests.IrisGribTest):
    def test_shape_unsupported(self):
        unsupported = [8, 9, 10, MDI]
        emsg = 'unsupported shape of the earth'
        for shape in unsupported:
            with self.assertRaisesRegex(TranslationError, emsg):
                ellipsoid(shape, MDI, MDI, MDI)

    def test_spherical_default_supported(self):
        cs_by_shape = {0: icoord_systems.GeogCS(6367470),
                       6: icoord_systems.GeogCS(6371229)}
        for shape, expected in cs_by_shape.items():
            result = ellipsoid(shape, MDI, MDI, MDI)
            self.assertEqual(result, expected)

    def test_spherical_shape_1_no_radius(self):
        shape = 1
        emsg = 'radius to be specified'
        with self.assertRaisesRegex(ValueError, emsg):
            ellipsoid(shape, MDI, MDI, MDI)

    def test_spherical_shape_1(self):
        shape = 1
        radius = 10
        result = ellipsoid(shape, MDI, MDI, radius)
        expected = icoord_systems.GeogCS(radius)
        self.assertEqual(result, expected)

    def test_oblate_shape_3_7_no_axes(self):
        for shape in [3, 7]:
            emsg = 'axis to be specified'
            with self.assertRaisesRegex(ValueError, emsg):
                ellipsoid(shape, MDI, MDI, MDI)

    def test_oblate_shape_3_7_no_major(self):
        for shape in [3, 7]:
            emsg = 'major axis to be specified'
            with self.assertRaisesRegex(ValueError, emsg):
                ellipsoid(shape, MDI, 1, MDI)

    def test_oblate_shape_3_7_no_minor(self):
        for shape in [3, 7]:
            emsg = 'minor axis to be specified'
            with self.assertRaisesRegex(ValueError, emsg):
                ellipsoid(shape, 1, MDI, MDI)

    def test_oblate_shape_3_7(self):
        for shape in [3, 7]:
            major, minor = 1, 10
            scale = 1
            result = ellipsoid(shape, major, minor, MDI)
            if shape == 3:
                # Convert km to m.
                scale = 1000
            expected = icoord_systems.GeogCS(major * scale, minor * scale)
            self.assertEqual(result, expected)


if __name__ == '__main__':
    tests.main()
