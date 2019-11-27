# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Test function :func:`iris_grib._load_convert.grib2_convert`."""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

import copy
from unittest import mock

import iris_grib
from iris_grib._load_convert import grib2_convert
from iris_grib.tests.unit import _make_test_message


class Test(tests.IrisGribTest):
    def setUp(self):
        this = 'iris_grib._load_convert'
        self.patch('{}.reference_time_coord'.format(this), return_value=None)
        self.patch('{}.grid_definition_section'.format(this))
        self.patch('{}.product_definition_section'.format(this))
        self.patch('{}.data_representation_section'.format(this))
        self.patch('{}.bitmap_section'.format(this))

    def test(self):
        sections = [{'discipline': mock.sentinel.discipline},       # section 0
                    {'centre': 'ecmf',                              # section 1
                     'tablesVersion': mock.sentinel.tablesVersion},
                    None,                                           # section 2
                    mock.sentinel.grid_definition_section,          # section 3
                    mock.sentinel.product_definition_section,       # section 4
                    mock.sentinel.data_representation_section,      # section 5
                    mock.sentinel.bitmap_section]                   # section 6
        field = _make_test_message(sections)
        metadata = {'factories': [], 'references': [],
                    'standard_name': None,
                    'long_name': None, 'units': None, 'attributes': {},
                    'cell_methods': [], 'dim_coords_and_dims': [],
                    'aux_coords_and_dims': []}
        expected = copy.deepcopy(metadata)
        centre = 'European Centre for Medium Range Weather Forecasts'
        expected['attributes'] = {'centre': centre}
        # The call being tested.
        grib2_convert(field, metadata)
        self.assertEqual(metadata, expected)
        this = iris_grib._load_convert
        this.reference_time_coord.assert_called_with(sections[1])
        this.grid_definition_section.assert_called_with(sections[3],
                                                        expected)
        args = (sections[4], expected, sections[0]['discipline'],
                sections[1]['tablesVersion'], None)
        this.product_definition_section.assert_called_with(*args)


if __name__ == '__main__':
    tests.main()
