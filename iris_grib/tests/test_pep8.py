# (C) British Crown Copyright 2013 - 2016, Met Office
#
# This file is part of iris-grib.
#
# iris-grib is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-grib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-grib.  If not, see <http://www.gnu.org/licenses/>.
"""
Unit tests for iris-grib pep8 conformance.

"""

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

import os
import unittest

import pep8

import iris_grib


class Test(unittest.TestCase):
    def test_pep8_conformance(self):
        pep8style = pep8.StyleGuide(quiet=False)
        excluded = ['_grib_cf_map.py', '_grib1_load_rules.py']
        for fname in excluded:
            path = '*{}{}'.format(os.path.sep, fname)
            pep8style.options.exclude.append(path)

        extra_exclude_fname = os.path.join(os.path.dirname(__file__),
                                           '.pep8_test_exclude.txt')

        if os.path.exists(extra_exclude_fname):
            with open(extra_exclude_fname) as fh:
                extra_exclude = [line.strip() for line in fh if line.strip()]
            pep8style.options.exclude.extend(extra_exclude)

        root = os.path.dirname(os.path.abspath(iris_grib.__file__))
        result = pep8style.check_files([root])
        emsg = 'Found code pep8 errors (and warnings).'
        self.assertEqual(result.total_errors, 0, emsg)


if __name__ == '__main__':
    unittest.main()
