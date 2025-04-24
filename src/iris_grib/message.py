# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Defines a lightweight wrapper class to wrap a single GRIB message.

"""

from collections import namedtuple
import re

import eccodes
import numpy as np
import numpy.ma as ma

from iris._lazy_data import as_lazy_data
from iris.exceptions import TranslationError

_SUPPORTED_GRID_DEFINITIONS = (0, 1, 5, 10, 12, 20, 30, 40, 90, 140)

# Alias names for eccodes spatial computed keys.
KEY_ALIAS = {
    "latitude": "latitudes",
    "longitude": "longitudes",
    "latitudes": "latitude",
    "longitudes": "longitude",
    # Support older form of key which used to exist before eccodes 2v36
    "indicatorOfUnitForForecastTime": "indicatorOfUnitOfTimeRange",
    # Support older name which became an alias at eccodes 2v38
    "numberOfTimeRange": "numberOfTimeRanges",
}


class _OpenFileRef:
    """
    A reference to an open file.

    This object ensures that the file is closed
    when the object is garbage collected.
    """

    def __init__(self, open_file):
        self.open_file = open_file

    def __del__(self):
        if not self.open_file.closed:
            self.open_file.close()


class GribMessage:
    """
    An in-memory representation of a GribMessage.

    Provides access to the :meth:`~GribMessage.data` payload and the metadata
    elements by section via the :meth:`~GribMessage.sections` property.

    """

    @staticmethod
    def messages_from_filename(filename):
        """
        Return the messages in a file.

        Return a generator of :class:`GribMessage` instances; one for
        each message in the supplied GRIB file.

        Args:

        * filename (string):
            Name of the file to generate fields from.


        """
        grib_fh = open(filename, "rb")
        # create an _OpenFileRef to manage the closure of the file handle
        file_ref = _OpenFileRef(grib_fh)

        while True:
            grib_id = eccodes.codes_new_from_file(grib_fh, eccodes.CODES_PRODUCT_GRIB)
            if grib_id is None:
                break
            offset = eccodes.codes_get_message_offset(grib_id)
            raw_message = _RawGribMessage(grib_id)
            recreate_raw = _MessageLocation(filename, offset)
            yield GribMessage(raw_message, recreate_raw, file_ref=file_ref)

    def __init__(self, raw_message, recreate_raw, file_ref=None):
        """
        Create a GribMessage.

        It is recommended to obtain GribMessage instances from the static method
        :meth:`~GribMessage.messages_from_filename`, rather than creating
        them directly.

        """
        # A RawGribMessage giving ecCodes access to the original grib message.
        self._raw_message = raw_message
        # A _MessageLocation which dask uses to read the message data array,
        # by which time this message may be dead and the original grib file
        # closed.
        self._recreate_raw = recreate_raw
        # An _OpenFileRef to keep the grib file open while this GribMessage is
        # alive, so that we can always use self._raw_message to fetch keys.
        self._file_ref = file_ref

    @property
    def sections(self):
        """
        Return the key-value pairs of the message keys.

        The key-value pairs are grouped by containing section.

        Sections in a message are indexed by GRIB section-number,
        and values in a section are indexed by key strings.

        .. For example::

            print(grib_message.sections[4]['parameterNumber'])
            grib_message.sections[1]['minute'] = 0

        """
        return self._raw_message.sections

    @property
    def bmdi(self):
        # Not sure of any cases where GRIB provides a fill value.
        # Default for fill value is None.
        return None

    def core_data(self):
        return self.data

    @property
    def data(self):
        """
        The data array from the GRIB message as a dask Array.

        The shape of the array will match the logical shape of the
        message's grid. For example, a simple global grid would be
        available as a 2-dimensional array with shape (Nj, Ni).

        """
        sections = self.sections
        grid_section = sections[3]
        if grid_section["sourceOfGridDefinition"] != 0:
            raise TranslationError(
                "Unsupported source of grid definition: {}".format(
                    grid_section["sourceOfGridDefinition"]
                )
            )

        reduced = (
            grid_section["numberOfOctectsForNumberOfPoints"] != 0
            or grid_section["interpretationOfNumberOfPoints"] != 0
        )
        template = grid_section["gridDefinitionTemplateNumber"]
        if reduced and template not in (40,):
            raise TranslationError(
                "Grid definition Section 3 contains unsupported quasi-regular grid."
            )

        if template in _SUPPORTED_GRID_DEFINITIONS:
            # We can ignore the first two bits (i-neg, j-pos) because
            # that is already captured in the coordinate values.
            if grid_section["scanningMode"] & 0x3F:
                msg = "Unsupported scanning mode: {}".format(
                    grid_section["scanningMode"]
                )
                raise TranslationError(msg)
            if template in (20, 30, 90):
                shape = (grid_section["Ny"], grid_section["Nx"])
            elif template == 140:
                shape = (
                    grid_section["numberOfPointsAlongYAxis"],
                    grid_section["numberOfPointsAlongXAxis"],
                )
            elif template == 40 and reduced:
                shape = (grid_section["numberOfDataPoints"],)
            else:
                shape = (grid_section["Nj"], grid_section["Ni"])

            dtype = np.dtype("f8")
            proxy = _DataProxy(shape, dtype, self._recreate_raw)

            as_lazy_kwargs = {}
            from . import _ASLAZYDATA_NEEDS_META, _make_dask_meta

            if _ASLAZYDATA_NEEDS_META:
                has_bitmap = 6 in sections
                meta = _make_dask_meta(shape, dtype, is_masked=has_bitmap)
                as_lazy_kwargs["meta"] = meta

            data = as_lazy_data(proxy, **as_lazy_kwargs)

        else:
            fmt = "Grid definition template {} is not supported"
            raise TranslationError(fmt.format(template))
        return data

    def __getstate__(self):
        """
        Alter state of object prior to pickle, ensure open file is closed.

        """
        if not self._file_ref.open_file.closed:
            self._file_ref.open_file.close()
        return self


class _MessageLocation(namedtuple("_MessageLocation", "filename offset")):
    """A reference to a specific GRIB message within a file."""

    __slots__ = ()

    def __call__(self):
        return _RawGribMessage.from_file_offset(self.filename, self.offset)


class _DataProxy:
    """A reference to the data payload of a single GRIB message."""

    __slots__ = ("dtype", "recreate_raw", "shape")

    def __init__(self, shape, dtype, recreate_raw):
        self.shape = shape
        self.dtype = dtype
        self.recreate_raw = recreate_raw

    @property
    def ndim(self):
        return len(self.shape)

    def _bitmap(self, bitmap_section):
        """
        Get the bitmap for the data from the message.

        The GRIB spec defines that the bitmap is composed of values 0 or 1, where:

            * 0: no data value at corresponding data point (data point masked).
            * 1: data value at corresponding data point (data point unmasked).

        The bitmap can take the following values:

            * 0: Bitmap applies to the data and is specified in this section
                 of this message.
            * 1-253: Bitmap applies to the data, is specified by originating
                     centre and is not specified in section 6 of this message.
            * 254: Bitmap applies to the data, is specified in an earlier
                   section 6 of this message and is not specified in this
                   section 6 of this message.
            * 255: Bitmap does not apply to the data.

        Only values 0 and 255 are supported.

        Returns the bitmap as a 1D array of length equal to the
        number of data points in the message.

        """
        # Reference GRIB2 Code Table 6.0.
        bitMapIndicator = bitmap_section["bitMapIndicator"]

        if bitMapIndicator == 0:
            bitmap = bitmap_section["bitmap"]
        elif bitMapIndicator == 255:
            bitmap = None
        else:
            msg = "Bitmap Section 6 contains unsupported bitmap indicator [{}]".format(
                bitMapIndicator
            )
            raise TranslationError(msg)
        return bitmap

    def __getitem__(self, keys):
        # N.B. Assumes that the validity of this interpretation
        # is checked before this proxy is created.

        message = self.recreate_raw()
        sections = message.sections
        data = None

        if 5 in sections:
            # Data Representation Section.
            if sections[5]["bitsPerValue"] == 0:
                # Auto-generate zero data of the expected shape and dtype, as
                # there is no data stored within the Data Section of this GRIB
                # message. Also flatten the result to 1-D for potential bitmap
                # post-processing.
                data = np.ravel(np.zeros(self.shape, dtype=self.dtype))

        if data is None:
            # Data Section.
            data = sections[7]["codedValues"]

        # Bit-map Section.
        bitmap_section = sections[6]
        bitmap = self._bitmap(bitmap_section)

        if bitmap is not None:
            # Note that bitmap and data are both 1D arrays at this point.
            if np.count_nonzero(bitmap) == data.shape[0]:
                # Only the non-masked values are included in codedValues.
                _data = np.empty(shape=bitmap.shape)
                _data[bitmap.astype(bool)] = data
                # `ma.masked_array` masks where input = 1, the opposite of
                # the behaviour specified by the GRIB spec.
                data = ma.masked_array(
                    _data, mask=np.logical_not(bitmap), fill_value=np.nan
                )
            else:
                msg = "Shapes of data and bitmap do not match."
                raise TranslationError(msg)

        data = data.reshape(self.shape)
        result = data.__getitem__(keys)

        return result

    def __repr__(self):
        msg = (
            "<{self.__class__.__name__} shape={self.shape} "
            "dtype={self.dtype!r} recreate_raw={self.recreate_raw!r} "
        )
        return msg.format(self=self)

    def __getstate__(self):
        return {attr: getattr(self, attr) for attr in self.__slots__}

    def __setstate__(self, state):
        for key, value in state.items():
            setattr(self, key, value)


class _RawGribMessage:
    """
    Lightweight GRIB message wrapper.

    This contains **only** the coded keys of the input GRIB message.
    I.E. excluding any "computed" keys.

    """

    _NEW_SECTION_KEY_MATCHER = re.compile(r"section([0-9]{1})Length")

    @staticmethod
    def from_file_offset(filename, offset):
        with open(filename, "rb") as f:
            f.seek(offset)
            message_id = eccodes.codes_new_from_file(f, eccodes.CODES_PRODUCT_GRIB)
            if message_id is None:
                fmt = "Invalid GRIB message: {} @ {}"
                raise RuntimeError(fmt.format(filename, offset))
        return _RawGribMessage(message_id)

    def __init__(self, message_id):
        """
        Create a _RawGribMessage object.

        This contains the **coded** keys from a
        GRIB message that is identified by the input message id.

        Args:

        * message_id:
            An integer generated by gribapi referencing a GRIB message within
            an open GRIB file.

        """
        self._message_id = message_id
        self._sections = None

    def __del__(self):
        """
        Release the ecCodes reference to the message at end of object's life.

        """
        eccodes.codes_release(self._message_id)

    @property
    def sections(self):
        """
        Return the key-value pairs of the message keys.

        The key-value pairs are grouped by containing section.

        Key-value pairs are collected into a dictionary of
        :class:`Section` objects. One such object is made for
        each section in the message, such that the section number is the
        object's key in the containing dictionary. Each object contains
        key-value pairs for all of the message keys in the given section.

        """
        if self._sections is None:
            self._sections = self._get_message_sections()
        return self._sections

    def _get_message_keys(self):
        """Create a generator of all the keys in the message."""

        keys_itr = eccodes.codes_keys_iterator_new(self._message_id)
        eccodes.codes_skip_computed(keys_itr)
        while eccodes.codes_keys_iterator_next(keys_itr):
            yield eccodes.codes_keys_iterator_get_name(keys_itr)
        eccodes.codes_keys_iterator_delete(keys_itr)

    def _get_message_sections(self):
        """
        Group keys by section.

        Returns a dictionary mapping section number to :class:`Section`
        instance.

        .. seealso::
            The sections property (:meth:`~sections`).

        """
        sections = {}
        # The first keys in a message are for the whole message and are
        # contained in section 0.
        section = new_section = 0
        section_keys = []

        for key_name in self._get_message_keys():
            # The `section<1-7>Length` keys mark the start of each new
            # section, except for section 8 which is marked by the key '7777'.
            key_match = re.match(self._NEW_SECTION_KEY_MATCHER, key_name)
            if key_match is not None:
                new_section = int(key_match.group(1))
            elif key_name == "7777":
                new_section = 8
            if section != new_section:
                sections[section] = Section(self._message_id, section, section_keys)
                section_keys = []
                section = new_section
            section_keys.append(key_name)
        sections[section] = Section(self._message_id, section, section_keys)
        return sections


class Section:
    """
    A Section of a GRIB message.

    This supports dictionary-like access to key values, using gribapi key strings.

    Values for keys may be changed using assignment but this does not
    write to the file.

    """

    # Keys are read from the file as required and values are cached.
    # Within GribMessage instances all keys will have been fetched

    def __init__(self, message_id, number, keys):
        self._message_id = message_id
        self._number = number
        self._keys = keys
        self._cache = {}

    def __repr__(self):
        items = []
        for key in self._keys:
            value = self._cache.get(key, "?")
            items.append("{}={}".format(key, value))
        return "<{} {}: {}>".format(type(self).__name__, self._number, ", ".join(items))

    def __getitem__(self, key):
        if key not in self._cache:
            if key == "numberOfSection":
                value = self._number
            else:
                if key not in self._keys:
                    key2 = KEY_ALIAS.get(key)
                    if key2 and key2 in self._keys:
                        key = key2
                    else:
                        emsg = f"{key} not defined in section {self._number}"
                        raise KeyError(emsg)
                value = self._get_key_value(key)

            self._cache[key] = value

        return self._cache[key]

    def __setitem__(self, key, value):
        # Allow the overwriting of any entry already in the _cache.
        if key in self._cache:
            self._cache[key] = value
        else:
            raise KeyError(
                "{!r} cannot be redefined in section {}".format(key, self._number)
            )

    def _get_key_value(self, key):
        """
        Get the value associated with the given key in the GRIB message.

        Args:

        * key:
            The GRIB key to retrieve the value of.

        Returns the value associated with the requested key in the GRIB
        message.

        """
        vector_keys = (
            "codedValues",
            "pv",
            "satelliteSeries",
            "satelliteNumber",
            "instrumentType",
            "scaleFactorOfCentralWaveNumber",
            "scaledValueOfCentralWaveNumber",
            "longitude",
            "latitude",
            "longitudes",
            "latitudes",
        )
        if key in vector_keys:
            res = eccodes.codes_get_array(self._message_id, key)
        elif key == "bitmap":
            # The bitmap is stored as contiguous boolean bits, one bit for each
            # data point. ecCodes returns these as strings, so it must be type-cast
            # to return an array of ints (0, 1).
            res = eccodes.codes_get_array(self._message_id, key, int)
        elif key in ("typeOfFirstFixedSurface", "typeOfSecondFixedSurface"):
            # By default these values are returned as unhelpful strings but
            # we can use int representation to compare against instead.
            res = self._get_value_or_missing(key, use_int=True)
        else:
            res = self._get_value_or_missing(key)
        return res

    def get_computed_key(self, key):
        """
        Get the computed value for a given key.

        Returns the value associated with the given key in the GRIB message.

        Args:

        * key:
            The GRIB key to retrieve the value of.

        Returns the value associated with the requested key in the GRIB
        message.

        """
        vector_keys = ("longitudes", "latitudes", "distinctLatitudes")
        if key in vector_keys:
            res = eccodes.codes_get_array(self._message_id, key)
        else:
            res = self._get_value_or_missing(key)
        return res

    def keys(self):
        """Return coded keys available in this Section."""
        return self._keys

    def _get_value_or_missing(self, key, use_int=False):
        """
        Return value of header element, or None if value is encoded as missing.

        Implementation of Regulations 92.1.4 and 92.1.5 via ECCodes.

        """
        if eccodes.codes_is_missing(self._message_id, key):
            result = None
        else:
            if use_int:
                result = eccodes.codes_get(self._message_id, key, int)
            else:
                result = eccodes.codes_get(self._message_id, key)
        return result
