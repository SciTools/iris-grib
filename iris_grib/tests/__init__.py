# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
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

try:
    from iris.tests import IrisTest_nometa as IrisTest
except ImportError:
    from iris.tests import IrisTest

from iris.tests import main, skip_data, get_data_path


#: Basepath for iris-grib test results.
_RESULT_PATH = os.path.join(os.path.dirname(__file__), 'results')

#: Basepath for iris-grib loadable test files.
_TESTDATA_PATH = os.path.join(os.path.dirname(__file__), 'testdata')


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

    @staticmethod
    def get_testdata_path(relative_path):
        """
        Returns the absolute path to a loadable test data file, when given the
        relative path as a string, or sequence of strings.

        """
        if not isinstance(relative_path, six.string_types):
            relative_path = os.path.join(*relative_path)
        return os.path.abspath(os.path.join(_TESTDATA_PATH, relative_path))
