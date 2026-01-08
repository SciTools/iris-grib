# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""Common pytest fixtures for iris-grib testing."""

from pathlib import Path

import pytest

import iris.tests._shared_utils as iris_testutils


_RESULTS_PATH = Path(__file__).parent.absolute() / "results"


@pytest.fixture(autouse=True)
def assert_CML(request):
    """A fixture returning a test assertion routine to do CML comparison.

    The fixture returns a wrapper function, which calls
    :func:`iris.tests._shared_utils.assertCML`.

    In principle, this may in future generate automatic reference filepaths, i.e. when
    called as just ``pt_assertCML(cubes)``, with no reference path args.
    However, **that usage mode is not yet implemented.**
    """

    def do_assert(*args, **kwargs):
        # doctor reference path, then pass through.
        def fix_path(reference_path):
            # reference path is either a pathstring, a sequence of dirnames to be joined
            # or `None` (when it should generate an automatic reference path).
            # N.B. but we don't yet support `None`!
            if reference_path is None:
                msg = "Default testfile names not yet implemented for iris-grib."
                raise ValueError(msg)
            if isinstance(reference_path, Path | str):
                # pass as-is
                result = reference_path
            elif isinstance(reference_path, list | tuple):
                # To use Iris' assertCDL, convert this to an **absolute path**
                #  (since otherwise it will be in iris/tests/results)
                result = _RESULTS_PATH
                for name in reference_path:
                    result = result / name
                result = str(result)
            else:
                msg = f"Unrecognised testfile specifier: {reference_path!r}."
                raise ValueError(msg)
            return result

        if len(args) >= 2:
            args = list(args)
            args[1] = fix_path(args[1])
            args = tuple(args)
        if "reference_path" in kwargs:
            kwargs["reference_path"] = fix_path(kwargs["reference_path"])
        return iris_testutils.assert_CML(request, *args, **kwargs)

    return do_assert
