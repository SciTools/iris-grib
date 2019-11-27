# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.projection centre.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris_grib._load_convert import projection_centre, ProjectionCentre


class Test(tests.IrisGribTest):
    def test_unset(self):
        expected = ProjectionCentre(False, False)
        self.assertEqual(projection_centre(0x0), expected)

    def test_bipolar_and_symmetric(self):
        expected = ProjectionCentre(False, True)
        self.assertEqual(projection_centre(0x40), expected)

    def test_south_pole_on_projection_plane(self):
        expected = ProjectionCentre(True, False)
        self.assertEqual(projection_centre(0x80), expected)

    def test_both(self):
        expected = ProjectionCentre(True, True)
        self.assertEqual(projection_centre(0xc0), expected)


if __name__ == '__main__':
    tests.main()
