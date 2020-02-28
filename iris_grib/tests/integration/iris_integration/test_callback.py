# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test that iris load callbacks work with iris-grib.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests


import iris
import iris.coords


class TestCallbacks(tests.IrisGribTest):
    def test_load_callback(self):
        # What this actually tests:
        #    1. iris.load works with grib (though the GRIB picker is in Iris)
        #    2. callbacks work with the grib loader
        #    3. grib loaded result matches a cube snapshot
        def load_callback(cube, field, filename):
            # GRIB2 loader callback : 'field' is a GribMessage, which
            # has 'sections'.
            cube.add_aux_coord(
                iris.coords.AuxCoord(
                    field.sections[1]["year"],
                    long_name="extra_year_number_coord",
                    units="no_unit",
                )
            )

        fname = tests.get_data_path(("GRIB", "global_t", "global.grib2"))
        cube = iris.load_cube(fname, callback=load_callback)
        self.assertCML(cube)


if __name__ == "__main__":
    tests.main()
