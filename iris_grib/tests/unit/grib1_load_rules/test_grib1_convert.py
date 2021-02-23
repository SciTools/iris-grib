# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Unit tests for :func:`iris_grib._grib1_load_rules.grib1_convert`."""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else
import iris_grib.tests as tests

import gribapi
from unittest import mock

from iris.aux_factory import HybridPressureFactory
from iris.exceptions import TranslationError
from iris.fileformats.rules import Reference

from iris_grib import GribWrapper
from iris_grib._grib1_load_rules import grib1_convert
from iris_grib.tests.unit import TestField


class TestBadEdition(tests.IrisGribTest):
    def test(self):
        message = mock.Mock(edition=2)
        emsg = 'GRIB edition 2 is not supported'
        with self.assertRaisesRegex(TranslationError, emsg):
            grib1_convert(message)


class TestBoundedTime(TestField):
    @staticmethod
    def is_forecast_period(coord):
        return (coord.standard_name == 'forecast_period' and
                coord.units == 'hours')

    @staticmethod
    def is_time(coord):
        return (coord.standard_name == 'time' and
                coord.units == 'hours since epoch')

    def assert_bounded_message(self, **kwargs):
        attributes = {'productDefinitionTemplateNumber': 0,
                      'edition': 1, '_forecastTime': 15,
                      '_forecastTimeUnit': 'hours',
                      'phenomenon_bounds': lambda u: (80, 120),
                      '_phenomenonDateTime': -1,
                      'table2Version': 9999,
                      '_originatingCentre': 'xxx',
                      }
        attributes.update(kwargs)
        message = mock.Mock(**attributes)
        self._test_for_coord(message, grib1_convert, self.is_forecast_period,
                             expected_points=[35],
                             expected_bounds=[[15, 55]])
        self._test_for_coord(message, grib1_convert, self.is_time,
                             expected_points=[100],
                             expected_bounds=[[80, 120]])

    def test_time_range_indicator_2(self):
        self.assert_bounded_message(timeRangeIndicator=2)

    def test_time_range_indicator_3(self):
        self.assert_bounded_message(timeRangeIndicator=3)

    def test_time_range_indicator_4(self):
        self.assert_bounded_message(timeRangeIndicator=4)

    def test_time_range_indicator_5(self):
        self.assert_bounded_message(timeRangeIndicator=5)

    def test_time_range_indicator_51(self):
        self.assert_bounded_message(timeRangeIndicator=51)

    def test_time_range_indicator_113(self):
        self.assert_bounded_message(timeRangeIndicator=113)

    def test_time_range_indicator_114(self):
        self.assert_bounded_message(timeRangeIndicator=114)

    def test_time_range_indicator_115(self):
        self.assert_bounded_message(timeRangeIndicator=115)

    def test_time_range_indicator_116(self):
        self.assert_bounded_message(timeRangeIndicator=116)

    def test_time_range_indicator_117(self):
        self.assert_bounded_message(timeRangeIndicator=117)

    def test_time_range_indicator_118(self):
        self.assert_bounded_message(timeRangeIndicator=118)

    def test_time_range_indicator_123(self):
        self.assert_bounded_message(timeRangeIndicator=123)

    def test_time_range_indicator_124(self):
        self.assert_bounded_message(timeRangeIndicator=124)

    def test_time_range_indicator_125(self):
        self.assert_bounded_message(timeRangeIndicator=125)


class Test_GribLevels(tests.IrisTest):
    def test_grib1_hybrid_height(self):
        gm = gribapi.grib_new_from_samples('regular_gg_ml_grib1')
        gw = GribWrapper(gm)
        results = grib1_convert(gw)

        factory, = results[0]
        self.assertEqual(factory.factory_class, HybridPressureFactory)
        delta, sigma, ref = factory.args
        self.assertEqual(delta, {'long_name': 'level_pressure'})
        self.assertEqual(sigma, {'long_name': 'sigma'})
        self.assertEqual(ref, Reference(name='surface_pressure'))

        coords_and_dims = results[8]
        coord, = [co for co, _ in coords_and_dims
                  if co.name() == 'model_level_number']
        self.assertEqual(coord.units, '1')
        self.assertEqual(coord.attributes['positive'], 'up')
        coord, = [co for co, _ in coords_and_dims
                  if co.name() == 'level_pressure']
        self.assertEqual(coord.units, 'Pa')
        coord, = [co for co, _ in coords_and_dims
                  if co.name() == 'sigma']
        self.assertEqual(coord.units, '1')


if __name__ == "__main__":
    tests.main()
