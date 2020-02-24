# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration tests for round-trip loading and saving various product
definitions.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from cf_units import Unit
from iris import load_cube, save
import iris.coords
import iris.coord_systems

import iris.tests.stock as stock

from iris_grib.grib_phenom_translation import GRIBCode


class TestPDT11(tests.TestGribMessage):
    def test_perturbation(self):
        path = tests.get_data_path(
            ("NetCDF", "global", "xyt", "SMALL_hires_wind_u_for_ipcc4.nc")
        )
        cube = load_cube(path)
        # trim to 1 time and regular lats
        cube = cube[0, 12:144, :]
        crs = iris.coord_systems.GeogCS(6371229)
        cube.coord("latitude").coord_system = crs
        cube.coord("longitude").coord_system = crs
        # add a realization coordinate
        cube.add_aux_coord(
            iris.coords.DimCoord(
                points=1, standard_name="realization", units="1"
            )
        )
        with self.temp_filename("testPDT11.GRIB2") as temp_file_path:
            iris.save(cube, temp_file_path)

            # Check that various aspects of the saved file are as expected.
            expect_values = (
                (0, "editionNumber", 2),
                (3, "gridDefinitionTemplateNumber", 0),
                (4, "productDefinitionTemplateNumber", 11),
                (4, "perturbationNumber", 1),
                (4, "typeOfStatisticalProcessing", 0),
                (4, "numberOfForecastsInEnsemble", 255),
            )
            self.assertGribMessageContents(temp_file_path, expect_values)


class TestPDT40(tests.IrisTest):
    def test_save_load(self):
        cube = stock.lat_lon_cube()
        cube.rename("atmosphere_mole_content_of_ozone")
        cube.units = Unit("Dobson")
        tcoord = iris.coords.DimCoord(
            23, "time", units=Unit("days since epoch", calendar="standard")
        )
        fpcoord = iris.coords.DimCoord(24, "forecast_period",
                                       units=Unit("hours"))
        cube.add_aux_coord(tcoord)
        cube.add_aux_coord(fpcoord)
        cube.attributes["WMO_constituent_type"] = 0
        cube.attributes["GRIB_PARAM"] = GRIBCode("GRIB2:d000c014n000")

        with self.temp_filename("test_grib_pdt40.grib2") as temp_file_path:
            save(cube, temp_file_path)
            loaded = load_cube(temp_file_path)
            self.assertEqual(loaded.attributes, cube.attributes)


if __name__ == "__main__":
    tests.main()
