# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""Conversion of cubes to/from GRIB.

See: `ECMWF ecCodes grib interface <https://confluence.ecmwf.int/display/ECC>`_.

"""

import contextlib

import eccodes
import numpy as np
import threading

# NOTE: careful here, to avoid circular imports (as iris imports grib)
import iris  # noqa: F401
from iris.exceptions import TranslationError

from . import _save_rules
from ._load_convert import convert as load_convert
from .message import GribMessage


try:
    from ._version import version as __version__
except ModuleNotFoundError:
    __version__ = "unknown"

__all__ = [
    "GRIB1_LOADING_MODE",
    "Grib1LoadingMode",
    "load_cubes",
    "load_pairs_from_fields",
    "save_grib2",
    "save_messages",
    "save_pairs_from_cube",
]


class Grib1LoadingMode(threading.local):
    """
    A control object selecting between "legacy" and "future" GRIB1 loading methods.

    This is designed to provide the singleton :data:`iris_grib.GRIB1_LOADING_MODE`
    object.  It provides :meth:`set` and :meth:`context` methods to control a binary
    switch to enable either the new, recommended "future" mode, or the legacy code.

    The "legacy" GRIB1 loading mode is based on the
    :class:`iris_grib._grib1_legacy.GribWrapper`, and makes extensive use of ecCodes
    'computed keys' facilities for a 'best efforts' approach to loading which does not
    rigorously test all metadata to interpret fields.
    The newer "strict" loading, by contrast, is based on the
    :class:`iris_grib.message.GribMessage` class and will raise errors when encountering
    any unsupported or unrecognised metadata elements : this aligns it with the code
    which has long since been used to load GRIB2 data.

    .. warning::

        The legacy implementation is now deprecated and will be removed in due course.
        However, for full backwards compatibility, the 'legacy' mode is
        **still the default**.
    """

    def __init__(self, legacy=True):
        self.set(legacy=legacy)

    @property
    def use_legacy_grib1_loading(self):
        """Tell whether "legacy" GRIB1 loading is in use.

        N.B. read-only property.  Use :meth:`set` to change.
        """
        return self._use_legacy_grib1_loading

    def set(self, *, legacy):
        """
        Permanently set the GRIB1 loading mode.

        Args:

        * legacy : bool
            Control whether "legacy" or "future" GRIB1 loading mode is used, for the
            duration of the context block.
            This keyword is required (must be present, and not positional).

        Example:

        .. testsetup::

            >>> import iris_grib
            >>> try:
            ...     from iris.tests._shared_utils import get_data_path
            ... except ImportError:
            ...     from iris.tests import get_data_path
            >>> # this is a bit of a cheat, as it doesn't include any GRIB1 data
            >>> path = get_data_path(("GRIB", "global_t", "global.grib2"))
            >>> old_legacy = iris_grib.GRIB1_LOADING_MODE.use_legacy_grib1_loading

        .. doctest::

            >>> iris_grib.GRIB1_LOADING_MODE.set(legacy=False)
            >>> cubes = iris_grib.load_cubes(path)

        .. testcleanup::

            >>> iris_grib.GRIB1_LOADING_MODE.set(legacy=old_legacy)

        .. note::

            The legacy implementation is now deprecated and will be removed in due
            course. However, for full backwwards compatibility, 'legacy' mode is still
            the default.

            You are advised to use ``iris_grib.GRIB1_LOADING_MODE.set(legacy=False)``
            at the top of the main script.

        .. warning::

            Do not set/unset this dynamically to control loading mode for the duration
            of some lines of code : this can cause incorrect operation in threaded
            loading operations.  For dynamic control, use :meth:`context` instead.

        """
        self._use_legacy_grib1_loading = legacy

    @contextlib.contextmanager
    def context(self, *, legacy):
        """
        Set the GRIB1 loading mode which applies during a context block.

        Args:

        * legacy : bool
            Control whether "legacy" or "future" GRIB1 loading mode is used, for the
            duration of the context block.
            This keyword is required (must be present, and not positional).

        Example:

        .. testsetup::

            >>> import iris_grib
            >>> try:
            ...     from iris.tests._shared_utils import get_data_path
            ... except ImportError:
            ...     from iris.tests import get_data_path
            >>> # this is a bit of a cheat, as it doesn't include any GRIB1 data
            >>> path = get_data_path(("GRIB", "global_t", "global.grib2"))

        .. doctest::

            >>> with iris_grib.GRIB1_LOADING_MODE.context(legacy=False):
            ...     cubes = iris_grib.load_cubes(path)

        """
        old_mode = self._use_legacy_grib1_loading
        try:
            self._use_legacy_grib1_loading = legacy
            yield
        finally:
            self._use_legacy_grib1_loading = old_mode

    def __repr__(self):
        return f"GRIB1_LOADING_MODE(legacy={self.use_legacy_grib1_loading})"


#: a global singleton object controlling the way in which GRIB1 data is loaded.
GRIB1_LOADING_MODE = Grib1LoadingMode()


# Utility routines for the use of dask 'meta' in wrapping proxies
def _aslazydata_has_meta():
    """Work out whether 'iris._lazy_data.as_lazy_data' takes a "meta" kwarg.

    Up to Iris 3.8.0, "as_lazy_data" did not have a 'meta' keyword, but
    since https://github.com/SciTools/iris/pull/5801, it now *requires* one,
    if the wrapped object is anything other than a numpy or dask array.
    """
    from inspect import signature  # noqa: PLC0415
    from iris._lazy_data import as_lazy_data  # noqa: PLC0415

    sig = signature(as_lazy_data)
    return "meta" in sig.parameters


# Work this out just once.
_ASLAZYDATA_NEEDS_META = _aslazydata_has_meta()


def _make_dask_meta(shape, dtype, is_masked=True):
    """Construct a dask 'meta' object for use in 'dask.array.from_array'.

    A "meta" array is made from the dtype and shape of the array-like to be
    wrapped, plus whether it will return masked or unmasked data.
    """
    meta_shape = tuple([0 for _ in shape])
    array_class = np.ma if is_masked else np
    meta = array_class.zeros(meta_shape, dtype=dtype)
    return meta


def _load_generate(filename):
    messages = GribMessage.messages_from_filename(filename)
    for message in messages:
        editionNumber = message.sections[0]["editionNumber"]
        if editionNumber == 1:
            if GRIB1_LOADING_MODE.use_legacy_grib1_loading:
                from ._grib1_legacy.grib_wrapper import GribWrapper  # noqa: PLC0415

                has_bitmap = 3 in message.sections
                message_id = message._raw_message._message_id
                grib_fh = message._file_ref.open_file
                message = GribWrapper(
                    message_id, grib_fh=grib_fh, has_bitmap=has_bitmap
                )
        elif editionNumber != 2:
            emsg = "GRIB edition {} is not supported by {!r}."
            raise TranslationError(emsg.format(editionNumber, type(message).__name__))
        yield message


def load_cubes(filenames, callback=None):
    """Return an iterator over cubes from the given list of filenames.

    Args:

    * filenames:
        One or more GRIB filenames to load from.

    Kwargs:

    * callback:
        Function which can be passed on to :func:`iris.io.run_callback`.

    Returns:
        An iterator returning Iris cubes loaded from the GRIB files.

    """
    import iris.fileformats.rules as iris_rules  # noqa: PLC0415

    grib_loader = iris_rules.Loader(_load_generate, {}, load_convert)
    return iris_rules.load_cubes(filenames, callback, grib_loader)


def load_pairs_from_fields(grib_messages):
    """Convert an GRIB messages into (Cube, Grib message) tuples.

    Parameters
    ----------
    grib_messages : iterable on (cube, message)
        An iterable of :class:`GribMessage`.

    Returns
    -------
    iterable of (cube, message)
        An iterable of (:class:`~iris.Cube`, :class:`GribMessage`),
        pairing each message with a corresponding generated cube.

    Notes
    -----
    This capability can be used to filter out fields before they are passed to
    the load pipeline, and amend the cubes once they are created, using
    GRIB metadata conditions.  Where the filtering
    removes a significant number of fields, the speed up to load can be
    significant:

        >>> import iris
        >>> from iris_grib import load_pairs_from_fields
        >>> from iris_grib.message import GribMessage
        >>> filename = iris.sample_data_path("polar_stereo.grib2")
        >>> filtered_messages = []
        >>> for message in GribMessage.messages_from_filename(filename):
        ...     if message.sections[1]["productionStatusOfProcessedData"] == 0:
        ...         filtered_messages.append(message)
        >>> cubes_messages = load_pairs_from_fields(filtered_messages)
        >>> for cube, msg in cubes_messages:
        ...     prod_stat = msg.sections[1]["productionStatusOfProcessedData"]
        ...     cube.attributes["productionStatusOfProcessedData"] = prod_stat
        >>> print(cube.attributes["productionStatusOfProcessedData"])
        0

    This capability can also be used to alter fields before they are passed to
    the load pipeline.  Fields with out of specification header elements can
    be cleaned up this way and cubes created:

        >>> from iris_grib import load_pairs_from_fields
        >>> cleaned_messages = GribMessage.messages_from_filename(filename)
        >>> for message in cleaned_messages:
        ...     if message.sections[1]["productionStatusOfProcessedData"] == 0:
        ...         message.sections[1]["productionStatusOfProcessedData"] = 4
        >>> cubes = load_pairs_from_fields(cleaned_messages)

    Args:

    * grib_messages:
        An iterable of :class:`iris_grib.message.GribMessage`.

    Returns:
        An iterable of tuples of (:class:`iris.cube.Cube`,
        :class:`iris_grib.message.GribMessage`).

    """
    import iris.fileformats.rules as iris_rules  # noqa: PLC0415

    return iris_rules.load_pairs_from_fields(grib_messages, load_convert)


def save_grib2(cube, target, append=False):
    """Save a cube or iterable of cubes to a GRIB2 file.

    Args:

    * cube:
        The :class:`iris.cube.Cube`, :class:`iris.cube.CubeList` or list of
        cubes to save to a GRIB2 file.
    * target:
        A filename or open file handle specifying the GRIB2 file to save
        to.

    Kwargs:

    * append:
        Whether to start a new file afresh or add the cube(s) to the end of
        the file. Only applicable when target is a filename, not a file
        handle. Default is False.

    """
    messages = (message for _, message in save_pairs_from_cube(cube))
    save_messages(messages, target, append=append)


def save_pairs_from_cube(cube):
    """Convert one or more cubes to (2D cube, GRIB-message-id) pairs.

    Produces pairs of 2D cubes and GRIB messages, the result of the 2D cube
    being processed by the GRIB save rules.

    Args:

    * cube:
        A :class:`iris.cube.Cube`, :class:`iris.cube.CubeList` or
        list of cubes.

    Returns:
        a iterator returning (cube, field) pairs, where each ``cube`` is a 2d
        slice of the input and each``field`` is an eccodes message "id".
        N.B. the message "id"s are integer handles.
    """
    x_coords = cube.coords(axis="x", dim_coords=True)
    y_coords = cube.coords(axis="y", dim_coords=True)
    if len(x_coords) != 1 or len(y_coords) != 1:
        raise TranslationError("Did not find one (and only one) x or y coord")

    # Save each latlon slice2D in the cube
    for slice2D in cube.slices([y_coords[0], x_coords[0]]):
        grib_message = eccodes.codes_grib_new_from_samples("GRIB2")
        _save_rules.run(slice2D, grib_message, cube)
        yield (slice2D, grib_message)


def save_messages(messages, target, append=False):
    """Save messages to a GRIB2 file.

    The messages will be released as part of the save.

    Args:

    * messages:
        An iterable of grib_api message IDs.
    * target:
        A filename or open file handle.

    Kwargs:

    * append:
        Whether to start a new file afresh or add the cube(s) to the end of
        the file. Only applicable when target is a filename, not a file
        handle. Default is False.

    """
    # grib file (this bit is common to the pp and grib savers...)
    if isinstance(target, str):
        grib_file = open(target, "ab" if append else "wb")
    elif hasattr(target, "write"):
        if hasattr(target, "mode") and "b" not in target.mode:
            raise ValueError("Target not binary")
        grib_file = target
    else:
        raise ValueError("Can only save grib to filename or writable")

    try:
        for message in messages:
            eccodes.codes_write(message, grib_file)
            eccodes.codes_release(message)
    finally:
        # (this bit is common to the pp and grib savers...)
        if isinstance(target, str):
            grib_file.close()
