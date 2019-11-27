# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Unit tests for the :mod:`iris_grib._load_convert` package."""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from collections import OrderedDict


def empty_metadata():
    metadata = OrderedDict()
    metadata['factories'] = []
    metadata['references'] = []
    metadata['standard_name'] = None
    metadata['long_name'] = None
    metadata['units'] = None
    metadata['attributes'] = {}
    metadata['cell_methods'] = []
    metadata['dim_coords_and_dims'] = []
    metadata['aux_coords_and_dims'] = []
    return metadata


class LoadConvertTest(tests.IrisGribTest):
    def assertMetadataEqual(self, result, expected):
        # Compare two metadata dictionaries. Gives slightly more
        # helpful error message than: self.assertEqual(result, expected)
        self.assertEqual(result.keys(), expected.keys())
        for key in result.keys():
            self.assertEqual(result[key], expected[key])
