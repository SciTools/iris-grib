# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.ellipsoid_geometry.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris_grib._load_convert import ellipsoid_geometry


class Test(tests.IrisGribTest):
    def setUp(self):
        self.section = {'scaledValueOfEarthMajorAxis': 10,
                        'scaleFactorOfEarthMajorAxis': 1,
                        'scaledValueOfEarthMinorAxis': 100,
                        'scaleFactorOfEarthMinorAxis': 2,
                        'scaledValueOfRadiusOfSphericalEarth': 1000,
                        'scaleFactorOfRadiusOfSphericalEarth': 3}

    def test_geometry(self):
        result = ellipsoid_geometry(self.section)
        self.assertEqual(result, (1.0, 1.0, 1.0))


if __name__ == '__main__':
    tests.main()
