# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for iris-grib pep8 conformance.

"""

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
