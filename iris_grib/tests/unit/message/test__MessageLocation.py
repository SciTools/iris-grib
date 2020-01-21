# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for the `iris.message._MessageLocation` class.

"""

# Import iris_grib.tests first so that some things can be initialised before
# importing anything else.
import iris_grib.tests as tests

from unittest import mock

from iris_grib.message import _MessageLocation


class Test(tests.IrisGribTest):
    def test(self):
        message_location = _MessageLocation(mock.sentinel.filename,
                                            mock.sentinel.location)
        patch_target = 'iris_grib.message._RawGribMessage.from_file_offset'
        expected = mock.sentinel.message
        with mock.patch(patch_target, return_value=expected) as rgm:
            result = message_location()
        rgm.assert_called_once_with(mock.sentinel.filename,
                                    mock.sentinel.location)
        self.assertIs(result, expected)


if __name__ == '__main__':
    tests.main()
