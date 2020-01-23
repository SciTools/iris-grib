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
            'Nx': 15,
            'Ny': 10,
            'latitudeOfFirstGridPoint': 53988880,
            'longitudeOfFirstGridPoint': -4027984,
            'standardParallelInMicrodegrees' : 54900000,
            'centralLongitudeInMicrodegrees' : -2500000,
            'resolutionAndComponentFlags': 0b00000000,
            'Dx': 2000000,
            'Dy': 2000000,
            'scanningMode': 0b01000000,
        }
        return section

    def expected(self, y_dim, x_dim):
        # Prepare the expectation.
        # TODO

    def test(self):
        # TODO


if __name__ == '__main__':
    tests.main()
