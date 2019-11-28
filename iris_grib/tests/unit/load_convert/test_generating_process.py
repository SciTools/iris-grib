# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for function
:func:`iris_grib._load_convert.generating_process`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris_grib._load_convert import generating_process


class TestGeneratingProcess(tests.IrisGribTest):
    def setUp(self):
        self.warn_patch = self.patch('warnings.warn')

    def test_nowarn(self):
        generating_process(None)
        self.assertEqual(self.warn_patch.call_count, 0)

    def _check_warnings(self, with_forecast=True):
        module = 'iris_grib._load_convert'
        self.patch(module + '.options.warn_on_unsupported', True)
        call_args = [None]
        call_kwargs = {}
        expected_fragments = [
            'Unable to translate type of generating process',
            'Unable to translate background generating process']
        if with_forecast:
            expected_fragments.append(
                'Unable to translate forecast generating process')
        else:
            call_kwargs['include_forecast_process'] = False
        generating_process(*call_args, **call_kwargs)
        got_msgs = [call[0][0] for call in self.warn_patch.call_args_list]
        for got_msg, expected_fragment in zip(sorted(got_msgs),
                                              sorted(expected_fragments)):
            self.assertIn(expected_fragment, got_msg)

    def test_warn_full(self):
        self._check_warnings()

    def test_warn_no_forecast(self):
        self._check_warnings(with_forecast=False)


if __name__ == '__main__':
    tests.main()
