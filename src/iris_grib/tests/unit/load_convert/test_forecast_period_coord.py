# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Test function :func:`iris_grib._load_convert.forecast_period_coord.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.coords import DimCoord

from iris_grib._load_convert import forecast_period_coord


class Test(tests.IrisGribTest):
    def test(self):
        # (indicatorOfUnitForForecastTime, forecastTime, expected-hours)
        times = [
            (0, 60, 1),  # minutes
            (1, 2, 2),  # hours
            (2, 1, 24),  # days
            (10, 2, 6),  # 3 hours
            (11, 3, 18),  # 6 hours
            (12, 2, 24),  # 12 hours
            (13, 3600, 1),
        ]  # seconds

        for indicatorOfUnitForForecastTime, forecastTime, hours in times:
            coord = forecast_period_coord(indicatorOfUnitForForecastTime, forecastTime)
            self.assertIsInstance(coord, DimCoord)
            self.assertEqual(coord.standard_name, "forecast_period")
            self.assertEqual(coord.units, "hours")
            self.assertEqual(coord.shape, (1,))
            self.assertEqual(coord.points[0], hours)
            self.assertFalse(coord.has_bounds())


if __name__ == "__main__":
    tests.main()
