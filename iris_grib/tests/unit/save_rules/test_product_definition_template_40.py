# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for :func:`iris_grib._save_rules.product_definition_template_40`

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

from cf_units import Unit
import gribapi

from iris.coords import DimCoord
import iris.tests.stock as stock

from iris_grib._save_rules import product_definition_template_40


class TestChemicalConstituentIdentifier(tests.IrisGribTest):
    def setUp(self):
        self.cube = stock.lat_lon_cube()
        # Rename cube to avoid warning about unknown discipline/parameter.
        self.cube.rename('atmosphere_mole_content_of_ozone')
        coord = DimCoord(24, 'time',
                         units=Unit('days since epoch', calendar='standard'))
        self.cube.add_aux_coord(coord)
        self.cube.attributes['WMO_constituent_type'] = 0

    @mock.patch.object(gribapi, 'grib_set')
    def test_constituent_type(self, mock_set):
        cube = self.cube

        product_definition_template_40(cube, mock.sentinel.grib)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'productDefinitionTemplateNumber', 40)
        mock_set.assert_any_call(mock.sentinel.grib,
                                 'constituentType', 0)


if __name__ == '__main__':
    tests.main()
