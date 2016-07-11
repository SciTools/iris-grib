# (C) British Crown Copyright 2010 - 2016, Met Office
#
# This file is part of iris-grib.
#
# iris-grib is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-grib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-grib.  If not, see <http://www.gnu.org/licenses/>.
"""
Provides testing capabilities and customisations specific to iris-grib.

This imports iris.tests, which requires to be done before anything else for
plot control reasons : see documentation there.

"""
from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa
import six

import iris.tests

import inspect
import os
import os.path

from iris.tests import IrisTest, main, skip_data, get_data_path


#: Basepath for iris-grib test results.
_RESULT_PATH = os.path.join(os.path.dirname(__file__), 'results')


class IrisGribTest(IrisTest):
    # A specialised version of an IrisTest that implements the correct
    # automatic paths for test results in iris-grib.

    @staticmethod
    def get_result_path(relative_path):
        """
        Returns the absolute path to a result file when given the relative path
        as a string, or sequence of strings.

        """
        if not isinstance(relative_path, six.string_types):
            relative_path = os.path.join(*relative_path)
        return os.path.abspath(os.path.join(_RESULT_PATH, relative_path))

    def result_path(self, basename=None, ext=''):
        """
        Return the full path to a test result, generated from the \
        calling file, class and, optionally, method.

        Optional kwargs :

            * basename    - File basename. If omitted, this is \
                            generated from the calling method.
            * ext         - Appended file extension.

        """
        if ext and not ext.startswith('.'):
            ext = '.' + ext

        # Generate the folder name from the calling file name.
        path = os.path.abspath(inspect.getfile(self.__class__))
        path = os.path.splitext(path)[0]
        sub_path = path.rsplit('iris_grib', 1)[1].split('tests', 1)[1][1:]

        # Generate the file name from the calling function name?
        if basename is None:
            stack = inspect.stack()
            for frame in stack[1:]:
                if 'test_' in frame[3]:
                    basename = frame[3].replace('test_', '')
                    break
        filename = basename + ext

        result = os.path.join(self.get_result_path(''),
                              sub_path.replace('test_', ''),
                              self.__class__.__name__.replace('Test_', ''),
                              filename)
        return result
