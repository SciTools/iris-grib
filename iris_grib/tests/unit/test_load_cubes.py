# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Unit tests for the `iris_grib.load_cubes` function."""

import iris_grib.tests as tests

from unittest import mock

from iris.fileformats.rules import Loader

import iris_grib
from iris_grib import load_cubes


class Test(tests.IrisGribTest):
    def test(self):
        generator = iris_grib._load_generate
        converter = iris_grib._load_convert.convert
        files = mock.sentinel.FILES
        callback = mock.sentinel.CALLBACK
        expected_result = mock.sentinel.RESULT
        with mock.patch('iris.fileformats.rules.load_cubes') as rules_load:
            rules_load.return_value = expected_result
            result = load_cubes(files, callback)
            kwargs = {}
            loader = Loader(generator, kwargs, converter)
            rules_load.assert_called_once_with(files, callback, loader)
            self.assertIs(result, expected_result)


@tests.skip_data
class Test_load_cubes(tests.IrisGribTest):

    def test_reduced_raw(self):
        # Loading a GRIB message defined on a reduced grid without
        # interpolating to a regular grid.
        gribfile = tests.get_data_path(
            ("GRIB", "reduced", "reduced_gg.grib2"))
        grib_generator = load_cubes(gribfile)
        self.assertCML(next(grib_generator))


if __name__ == "__main__":
    tests.main()
