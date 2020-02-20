# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""Unit tests for the `iris_grib.load_pairs_from_fields` function."""

import iris_grib.tests as tests

from iris_grib import load_pairs_from_fields
from iris_grib.message import GribMessage


class TestAsCubes(tests.IrisTest):
    def setUp(self):
        # Load from the test file.
        self.file_path = tests.get_data_path(
            ("GRIB", "time_processed", "time_bound.grib2")
        )

    def test_year_filter(self):
        msgs = GribMessage.messages_from_filename(self.file_path)
        chosen_messages = []
        for gmsg in msgs:
            if gmsg.sections[1]["year"] == 1998:
                chosen_messages.append(gmsg)
        cubes_msgs = list(load_pairs_from_fields(chosen_messages))
        self.assertEqual(len(cubes_msgs), 1)

    def test_year_filter_none(self):
        msgs = GribMessage.messages_from_filename(self.file_path)
        chosen_messages = []
        for gmsg in msgs:
            if gmsg.sections[1]["year"] == 1958:
                chosen_messages.append(gmsg)
        cubes_msgs = list(load_pairs_from_fields(chosen_messages))
        self.assertEqual(len(cubes_msgs), 0)

    def test_as_pairs(self):
        messages = GribMessage.messages_from_filename(self.file_path)
        cubes = []
        cube_msg_pairs = load_pairs_from_fields(messages)
        for cube, gmsg in cube_msg_pairs:
            if gmsg.sections[1]["year"] == 1998:
                cube.attributes["the year is"] = gmsg.sections[1]["year"]
                cubes.append(cube)
        self.assertEqual(len(cubes), 1)
        self.assertEqual(cubes[0].attributes["the year is"], 1998)


if __name__ == "__main__":
    tests.main()
