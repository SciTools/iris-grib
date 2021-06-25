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

import iris.tests  # noqa: F401

import inspect
import os
import os.path
import unittest

import numpy as np

try:
    from iris.tests import IrisTest_nometa as IrisTest
except ImportError:
    from iris.tests import IrisTest

from iris.tests import main, skip_data, get_data_path  # noqa: F401

from iris_grib.message import GribMessage


#: Basepath for iris-grib test results.
_RESULT_PATH = os.path.join(os.path.dirname(__file__), 'results')

#: Basepath for iris-grib loadable test files.
_TESTDATA_PATH = os.path.join(os.path.dirname(__file__), 'testdata')

override = os.environ.get("GRIB_TEST_DATA_PATH")
if override:
    if os.path.isdir(os.path.expanduser(override)):
        _TESTDATA_PATH = os.path.abspath(override)


def skip_grib_data(fn):
    """
    Decorator to choose whether to run tests, based on the availability of
    external data.

    Example usage:
        @skip_data
        class MyDataTests(tests.IrisGribTest):
            ...

    """
    dpath = _TESTDATA_PATH
    evar = "GRIB_TEST_NO_DATA"
    no_data = not os.path.isdir(dpath) or os.environ.get(evar)
    reason = "Test(s) require missing external GRIB test data."

    skip = unittest.skipIf(
        condition=no_data, reason=reason
    )

    return skip(fn)


class IrisGribTest(IrisTest):
    # A specialised version of an IrisTest that implements the correct
    # automatic paths for test results in iris-grib.

    @staticmethod
    def get_result_path(relative_path):
        """
        Returns the absolute path to a result file when given the relative path
        as a string, or sequence of strings.

        """
        if not isinstance(relative_path, str):
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
        if not isinstance(relative_path, str):
            relative_path = os.path.join(*relative_path)
        return os.path.abspath(os.path.join(_TESTDATA_PATH, relative_path))


class TestGribMessage(IrisGribTest):
    def assertGribMessageContents(self, filename, contents):
        """
        Evaluate whether all messages in a GRIB2 file contain the provided
        contents.

        * filename (string)
            The path on disk of an existing GRIB file

        * contents
            An iterable of GRIB message keys and expected values.

        """
        messages = GribMessage.messages_from_filename(filename)
        for message in messages:
            for element in contents:
                section, key, val = element
                self.assertEqual(message.sections[section][key], val)

    def assertGribMessageDifference(
        self, filename1, filename2, diffs, skip_keys=(), skip_sections=()
    ):
        """
        Evaluate that the two messages only differ in the ways specified.

        * filename[0|1] (string)
            The path on disk of existing GRIB files

        * diffs
            An dictionary of GRIB message keys and expected diff values:
            {key: (m1val, m2val),...} .

        * skip_keys
            An iterable of key names to ignore during comparison.

        * skip_sections
            An iterable of section numbers to ignore during comparison.

        """
        messages1 = list(GribMessage.messages_from_filename(filename1))
        messages2 = list(GribMessage.messages_from_filename(filename2))
        self.assertEqual(len(messages1), len(messages2))
        for m1, m2 in zip(messages1, messages2):
            m1_sect = set(m1.sections.keys())
            m2_sect = set(m2.sections.keys())

            for missing_section in m1_sect ^ m2_sect:
                what = (
                    "introduced" if missing_section in m1_sect else "removed"
                )
                # Assert that an introduced section is in the diffs.
                self.assertIn(
                    missing_section,
                    skip_sections,
                    msg="Section {} {}".format(missing_section, what),
                )

            for section in m1_sect & m2_sect:
                # For each section, check that the differences are
                # known diffs.
                m1_keys = set(m1.sections[section]._keys)
                m2_keys = set(m2.sections[section]._keys)

                difference = m1_keys ^ m2_keys
                unexpected_differences = difference - set(skip_keys)
                if unexpected_differences:
                    self.fail(
                        "There were keys in section {} which \n"
                        "weren't in both messages and which weren't "
                        "skipped.\n{}"
                        "".format(section, ", ".join(unexpected_differences))
                    )

                keys_to_compare = m1_keys & m2_keys - set(skip_keys)

                for key in keys_to_compare:
                    m1_value = m1.sections[section][key]
                    m2_value = m2.sections[section][key]
                    msg = "{} {} != {}"
                    if key not in diffs:
                        # We have a key which we expect to be the same for
                        # both messages.
                        if isinstance(m1_value, np.ndarray):
                            # A large tolerance appears to be required for
                            # gribapi 1.12, but not for 1.14.
                            self.assertArrayAlmostEqual(
                                m1_value, m2_value, decimal=2
                            )
                        else:
                            self.assertEqual(
                                m1_value,
                                m2_value,
                                msg=msg.format(key, m1_value, m2_value),
                            )
                    else:
                        # We have a key which we expect to be different
                        # for each message.
                        self.assertEqual(
                            m1_value,
                            diffs[key][0],
                            msg=msg.format(key, m1_value, diffs[key][0]),
                        )

                        self.assertEqual(
                            m2_value,
                            diffs[key][1],
                            msg=msg.format(key, m2_value, diffs[key][1]),
                        )
