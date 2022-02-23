# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function
:func:`iris_grib._load_convert.ensemble_identifier`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from unittest import mock
import warnings

from iris.coords import DimCoord

from iris_grib._load_convert import ensemble_identifier


class Test(tests.IrisGribTest):
    def setUp(self):
        self.patch('warnings.warn')

    def _check(self, request_warning):
        section = {'perturbationNumber': 17}
        this = 'iris_grib._load_convert.options'
        with mock.patch(this, warn_on_unsupported=request_warning):
            realization = ensemble_identifier(section)
            expected = DimCoord(section['perturbationNumber'],
                                standard_name='realization',
                                units='no_unit')
            self.assertEqual(realization, expected)

            if request_warning:
                warn_msgs = [mcall[1][0] for mcall in warnings.warn.mock_calls]
                expected_msgs = ['type of ensemble', 'number of forecasts']
                for emsg in expected_msgs:
                    matches = [wmsg for wmsg in warn_msgs if emsg in wmsg]
                    self.assertEqual(len(matches), 1)
                    warn_msgs.remove(matches[0])
            else:
                self.assertEqual(len(warnings.warn.mock_calls), 0)

    def test_ens_no_warn(self):
        self._check(False)

    def test_ens_warn(self):
        self._check(True)


if __name__ == '__main__':
    tests.main()
