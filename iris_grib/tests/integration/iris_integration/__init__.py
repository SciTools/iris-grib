# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration tests confirming that iris functionality is working with GRIB
files.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests


import iris
import iris.coords


class TestCallbacks(tests.IrisGribTest):
    def test_grib_callback(self):
        def grib_thing_getter(cube, field, filename):
            if hasattr(field, "sections"):
                # New-style loader callback : 'field' is a GribMessage, which has 'sections'.
                cube.add_aux_coord(
                    iris.coords.AuxCoord(
                        field.sections[1]["year"],
                        long_name="extra_year_number_coord",
                        units="no_unit",
                    )
                )
            else:
                # Old-style loader provides 'GribWrapper' type field.
                cube.add_aux_coord(
                    iris.coords.AuxCoord(
                        field.extra_keys["_periodStartDateTime"],
                        long_name="random element",
                        units="no_unit",
                    )
                )

        fname = tests.get_data_path(("GRIB", "global_t", "global.grib2"))
        cube = iris.load_cube(fname, callback=grib_thing_getter)
        self.assertCML(cube)


if __name__ == "__main__":
    tests.main()