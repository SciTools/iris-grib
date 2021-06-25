# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for iris-grib license header conformance.

"""

from datetime import datetime
from fnmatch import fnmatch
import os
import subprocess
import unittest

import iris_grib


LICENSE_TEMPLATE = """# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details."""

# Guess iris-grib repo directory of Iris-grib - realpath is used to mitigate
# against Python finding the iris-grib package via a symlink.
IRIS_GRIB_DIR = os.path.realpath(os.path.dirname(iris_grib.__file__))
REPO_DIR = os.path.dirname(IRIS_GRIB_DIR)


class TestLicenseHeaders(unittest.TestCase):
    @staticmethod
    def whatchanged_parse(whatchanged_output):
        """
        Returns a generator of tuples of data parsed from
        "git whatchanged --pretty='TIME:%at". The tuples are of the form
        ``(filename, last_commit_datetime)``

        Sample input::

            ['TIME:1366884020', '',
             ':000000 100644 0000000... 5862ced... A\tlib/iris/cube.py']

        """
        dt = None
        for line in whatchanged_output:
            if not line.strip():
                continue
            elif line.startswith('TIME:'):
                dt = datetime.fromtimestamp(int(line[5:]))
            else:
                # Non blank, non date, line -> must be the lines
                # containing the file info.
                fname = ' '.join(line.split('\t')[1:])
                yield fname, dt

    @staticmethod
    def last_change_by_fname():
        """
        Return a dictionary of all the files under git which maps to
        the datetime of their last modification in the git history.

        .. note::

            This function raises a ValueError if the repo root does
            not have a ".git" folder. If git is not installed on the system,
            or cannot be found by subprocess, an IOError may also be raised.

        """
        # Check the ".git" folder exists at the repo dir.
        if not os.path.isdir(os.path.join(REPO_DIR, '.git')):
            raise ValueError('{} is not a git repository.'.format(REPO_DIR))

        # Call "git whatchanged" to get the details of all the files and when
        # they were last changed.
        output = subprocess.check_output(['git', 'whatchanged',
                                          "--pretty=TIME:%ct"],
                                         cwd=REPO_DIR)
        output = output.decode().split('\n')
        res = {}
        for fname, dt in TestLicenseHeaders.whatchanged_parse(output):
            if fname not in res or dt > res[fname]:
                res[fname] = dt

        return res

    def test_license_headers(self):
        exclude_patterns = ('setup.py',
                            'build/*',
                            'dist/*',
                            'docs/*',
                            'iris_grib/tests/unit/results/*',
                            'iris_grib.egg-info/*')

        try:
            last_change_by_fname = self.last_change_by_fname()
        except ValueError:
            # Caught the case where this is not a git repo.
            return self.skipTest('Iris-grib installation did not look like a '
                                 'git repo.')

        failed = False
        for fname, last_change in sorted(last_change_by_fname.items()):
            full_fname = os.path.join(REPO_DIR, fname)
            if full_fname.endswith('.py') and os.path.isfile(full_fname) and \
                    not any(fnmatch(fname, pat) for pat in exclude_patterns):
                with open(full_fname) as fh:
                    content = fh.read()
                    if not content.startswith(LICENSE_TEMPLATE):
                        print('The file {} does not start with the required '
                              'license header.'.format(fname))
                        failed = True

        if failed:
            raise ValueError('There were license header failures. See stdout.')


if __name__ == '__main__':
    unittest.main()
