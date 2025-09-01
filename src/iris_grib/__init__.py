# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""Conversion of cubes to/from GRIB.

See: `ECMWF ecCodes grib interface <https://confluence.ecmwf.int/display/ECC>`_.

"""

import datetime
import math  # for fmod

import cartopy.crs as ccrs
import cf_units
import eccodes
import numpy as np
import numpy.ma as ma

# NOTE: careful here, to avoid circular imports (as iris imports grib)
import iris  # noqa: F401
from iris._lazy_data import as_lazy_data
import iris.coord_systems as coord_systems
from iris.exceptions import TranslationError, NotYetImplementedError

from . import grib_phenom_translation as gptx
from . import _save_rules
from ._load_convert import convert as load_convert
from .message import GribMessage


try:
    from ._version import version as __version__
except ModuleNotFoundError:
    __version__ = "unknown"

__all__ = [
    "load_cubes",
    "load_pairs_from_fields",
    "save_grib2",
    "save_messages",
    "save_pairs_from_cube",
]


CENTRE_TITLES = {
    "egrr": "U.K. Met Office - Exeter",
    "ecmf": "European Centre for Medium Range Weather Forecasts",
    "rjtd": "Tokyo, Japan Meteorological Agency",
    "55": "San Francisco",
    "kwbc": (
        "US National Weather Service, National Centres for Environmental Prediction"
    ),
}

TIME_RANGE_INDICATORS = {
    0: "none",
    1: "none",
    3: "time mean",
    4: "time sum",
    5: "time _difference",
    10: "none",
    # TODO #567 Further exploration of following mappings
    51: "time mean",
    113: "time mean",
    114: "time sum",
    115: "time mean",
    116: "time sum",
    117: "time mean",
    118: "time _covariance",
    123: "time mean",
    124: "time sum",
    125: "time standard_deviation",
}

PROCESSING_TYPES = {
    0: "time mean",
    1: "time sum",
    2: "time maximum",
    3: "time minimum",
    4: "time _difference",
    5: "time _root mean square",
    6: "time standard_deviation",
    7: "time _convariance",
    8: "time _difference",
    9: "time _ratio",
}

TIME_CODES_EDITION1 = {
    0: ("minutes", 60),
    1: ("hours", 60 * 60),
    2: ("days", 24 * 60 * 60),
    # NOTE: do *not* support calendar-dependent units at all.
    # So the following possible keys remain unsupported:
    #  3: 'months',
    #  4: 'years',
    #  5: 'decades',
    #  6: '30 years',
    #  7: 'century',
    10: ("3 hours", 3 * 60 * 60),
    11: ("6 hours", 6 * 60 * 60),
    12: ("12 hours", 12 * 60 * 60),
    13: ("15 minutes", 15 * 60),
    14: ("30 minutes", 30 * 60),
    254: ("seconds", 1),
}

unknown_string = "???"


class GribDataProxy:
    """A reference to the data payload of a single Grib message."""

    __slots__ = ("dtype", "offset", "path", "shape")

    def __init__(self, shape, dtype, path, offset):
        self.shape = shape
        self.dtype = dtype
        self.path = path
        self.offset = offset

    @property
    def ndim(self):
        return len(self.shape)

    def __getitem__(self, keys):
        with open(self.path, "rb") as grib_fh:
            grib_fh.seek(self.offset)
            grib_message = eccodes.codes_new_from_file(
                grib_fh, eccodes.CODES_PRODUCT_GRIB
            )
            data = _message_values(grib_message, self.shape)
            eccodes.codes_release(grib_message)

        result = data.__getitem__(keys)

        return result

    def __repr__(self):
        msg = (
            "<{self.__class__.__name__} shape={self.shape} "
            "dtype={self.dtype!r} "
            "path={self.path!r} offset={self.offset}>"
        )
        return msg.format(self=self)

    def __getstate__(self):
        return {attr: getattr(self, attr) for attr in self.__slots__}

    def __setstate__(self, state):
        for key, value in state.items():
            setattr(self, key, value)


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


class GribWrapper:
    """Contains a pygrib object plus some extra keys of our own.

    The class :class:`iris_grib.message.GribMessage`
    provides alternative means of working with GRIB message instances.

    """

    def __init__(self, grib_message, grib_fh=None, has_bitmap=True):
        """Store the grib message and compute our extra keys."""
        self.grib_message = grib_message

        if self.edition != 1:
            emsg = "GRIB edition {} is not supported by {!r}."
            raise TranslationError(emsg.format(self.edition, type(self).__name__))

        deferred = grib_fh is not None

        # Store the file pointer and message length from the current
        # grib message before it's changed by calls to the grib-api.
        if deferred:
            offset = eccodes.codes_get_message_offset(grib_message)

        # Initialise the key-extension dictionary.
        # NOTE: this attribute *must* exist, or the the __getattr__ overload
        # can hit an infinite loop.
        self.extra_keys = {}
        self._confirm_in_scope()
        self._compute_extra_keys()

        # Calculate the data payload shape.
        shape = (eccodes.codes_get_long(grib_message, "numberOfValues"),)

        if not self.gridType.startswith("reduced"):
            ni, nj = self.Ni, self.Nj
            j_fast = eccodes.codes_get_long(grib_message, "jPointsAreConsecutive")
            shape = (nj, ni) if j_fast == 0 else (ni, nj)

        if deferred:
            # Wrap the reference to the data payload within the data proxy
            # in order to support deferred data loading.
            dtype = np.dtype(float)  # Use default dtype for python float
            proxy = GribDataProxy(shape, dtype, grib_fh.name, offset)
            as_lazy_kwargs = {}
            if _ASLAZYDATA_NEEDS_META:
                meta = _make_dask_meta(shape, dtype, is_masked=has_bitmap)
                as_lazy_kwargs["meta"] = meta
            self._data = as_lazy_data(proxy, **as_lazy_kwargs)
        else:
            self.data = _message_values(grib_message, shape)

    def _confirm_in_scope(self):
        """Ensure we have a grib flavour that we choose to support."""

        # forbid alternate row scanning
        # (uncommon entry from GRIB2 flag table 3.4, also in GRIB1)
        if self.alternativeRowScanning == 1:
            raise ValueError("alternativeRowScanning == 1 not handled.")

    def __getattr__(self, key):
        """Return a grib key, or one of our extra keys."""

        # is it in the grib message?
        try:
            # we just get <type 'float'> as the type of the "values"
            # array...special case here...
            if key in ["values", "pv", "latitudes", "longitudes"]:
                res = eccodes.codes_get_double_array(self.grib_message, key)
            elif key in ("typeOfFirstFixedSurface", "typeOfSecondFixedSurface"):
                res = np.int32(eccodes.codes_get_long(self.grib_message, key))
            else:
                key_type = eccodes.codes_get_native_type(self.grib_message, key)
                if key_type is int:
                    res = np.int32(eccodes.codes_get_long(self.grib_message, key))
                elif key_type is float:
                    # Because some computer keys are floats, like
                    # longitudeOfFirstGridPointInDegrees, a float32
                    # is not always enough...
                    res = np.float64(eccodes.codes_get_double(self.grib_message, key))
                elif key_type is str:
                    res = eccodes.codes_get_string(self.grib_message, key)
                else:
                    emsg = "Unknown type for {} : {}"
                    raise ValueError(emsg.format(key, str(key_type)))
        except eccodes.CodesInternalError:
            res = None

        # ...or is it in our list of extras?
        if res is None:
            if key in self.extra_keys:
                res = self.extra_keys[key]
            else:
                # must raise an exception for the hasattr() mechanism to work
                raise AttributeError("Cannot find GRIB key %s" % key)

        return res

    def _timeunit_detail(self):
        """Return the (string, seconds) describing the message time unit."""
        unit_code = self.indicatorOfUnitOfTimeRange
        if unit_code not in TIME_CODES_EDITION1:
            message = (
                "Unhandled time unit for forecast "
                "indicatorOfUnitOfTimeRange : " + str(unit_code)
            )
            raise NotYetImplementedError(message)
        return TIME_CODES_EDITION1[unit_code]

    def _timeunit_string(self):
        """Get the udunits string for the message time unit."""
        return self._timeunit_detail()[0]

    def _timeunit_seconds(self):
        """Get the number of seconds in the message time unit."""
        return self._timeunit_detail()[1]

    def _compute_extra_keys(self):
        """Compute our extra keys."""
        global unknown_string

        self.extra_keys = {}
        forecastTime = self.startStep

        # regular or rotated grid?
        try:
            longitudeOfSouthernPoleInDegrees = self.longitudeOfSouthernPoleInDegrees
            latitudeOfSouthernPoleInDegrees = self.latitudeOfSouthernPoleInDegrees
        except AttributeError:
            longitudeOfSouthernPoleInDegrees = 0.0
            latitudeOfSouthernPoleInDegrees = 90.0

        centre = eccodes.codes_get_string(self.grib_message, "centre")

        # default values
        self.extra_keys = {
            "_referenceDateTime": -1.0,
            "_phenomenonDateTime": -1.0,
            "_periodStartDateTime": -1.0,
            "_periodEndDateTime": -1.0,
            "_levelTypeName": unknown_string,
            "_levelTypeUnits": unknown_string,
            "_firstLevelTypeName": unknown_string,
            "_firstLevelTypeUnits": unknown_string,
            "_firstLevel": -1.0,
            "_secondLevelTypeName": unknown_string,
            "_secondLevel": -1.0,
            "_originatingCentre": unknown_string,
            "_forecastTime": None,
            "_forecastTimeUnit": unknown_string,
            "_coord_system": None,
            "_x_circular": False,
            "_x_coord_name": unknown_string,
            "_y_coord_name": unknown_string,
            # These are here to avoid repetition in the rules
            # files, and reduce the very long line lengths.
            "_x_points": None,
            "_y_points": None,
            "_cf_data": None,
            "_grib_code": None,
        }

        # cf phenomenon translation
        # Get centre code (N.B. self.centre has default type = string)
        centre_number = eccodes.codes_get_long(self.grib_message, "centre")
        # Look for a known grib1-to-cf translation (or None).
        cf_data = gptx.grib1_phenom_to_cf_info(
            table2_version=self.table2Version,
            centre_number=centre_number,
            param_number=self.indicatorOfParameter,
        )
        self.extra_keys["_cf_data"] = cf_data

        # Record the original parameter encoding
        self.extra_keys["_grib_code"] = gptx.GRIBCode(
            edition=1,
            table_version=self.table2Version,
            centre_number=centre_number,
            number=self.indicatorOfParameter,
        )

        # reference date
        self.extra_keys["_referenceDateTime"] = datetime.datetime(
            int(self.year),
            int(self.month),
            int(self.day),
            int(self.hour),
            int(self.minute),
        )

        # forecast time with workarounds
        self.extra_keys["_forecastTime"] = forecastTime

        # verification date
        processingDone = self._get_processing_done()
        # time processed?
        if processingDone.startswith("time"):
            validityDate = str(self.validityDate)
            validityTime = "{:04}".format(int(self.validityTime))
            endYear = int(validityDate[:4])
            endMonth = int(validityDate[4:6])
            endDay = int(validityDate[6:8])
            endHour = int(validityTime[:2])
            endMinute = int(validityTime[2:4])

            # fixed forecastTime in hours
            self.extra_keys["_periodStartDateTime"] = self.extra_keys[
                "_referenceDateTime"
            ] + datetime.timedelta(hours=int(forecastTime))
            self.extra_keys["_periodEndDateTime"] = datetime.datetime(
                endYear, endMonth, endDay, endHour, endMinute
            )
        else:
            self.extra_keys["_phenomenonDateTime"] = self._get_verification_date()

        # originating centre
        # TODO #574 Expand to include sub-centre
        self.extra_keys["_originatingCentre"] = CENTRE_TITLES.get(
            centre, "unknown centre %s" % centre
        )

        # forecast time unit as a cm string
        # TODO #575 Do we want PP or GRIB style forecast delta?
        self.extra_keys["_forecastTimeUnit"] = self._timeunit_string()

        # shape of the Earth
        oblate_Earth = self.resolutionAndComponentFlags & 0b0100000
        if oblate_Earth:
            # Earth assumed oblate spheroidal with size as determined by IAU in
            # 1965 (6378.160 km, 6356.775 km, f = 1/297.0)
            raise ValueError("Oblate Spheroidal Earth is not supported.")
        else:
            # Earth assumed spherical with radius 6367.47 km
            geoid = coord_systems.GeogCS(semi_major_axis=6367470)

        gridType = eccodes.codes_get_string(self.grib_message, "gridType")

        if gridType in ["regular_ll", "regular_gg", "reduced_ll", "reduced_gg"]:
            self.extra_keys["_x_coord_name"] = "longitude"
            self.extra_keys["_y_coord_name"] = "latitude"
            self.extra_keys["_coord_system"] = geoid
        elif gridType == "rotated_ll":
            # TODO: Confirm the translation from angleOfRotation to
            # north_pole_lon (usually 0 for both)
            self.extra_keys["_x_coord_name"] = "grid_longitude"
            self.extra_keys["_y_coord_name"] = "grid_latitude"
            southPoleLon = longitudeOfSouthernPoleInDegrees
            southPoleLat = latitudeOfSouthernPoleInDegrees
            self.extra_keys["_coord_system"] = coord_systems.RotatedGeogCS(
                -southPoleLat,
                math.fmod(southPoleLon + 180.0, 360.0),
                self.angleOfRotation,
                geoid,
            )
        elif gridType == "polar_stereographic":
            self.extra_keys["_x_coord_name"] = "projection_x_coordinate"
            self.extra_keys["_y_coord_name"] = "projection_y_coordinate"

            if self.projectionCentreFlag == 0:
                pole_lat = 90
            elif self.projectionCentreFlag == 1:
                pole_lat = -90
            else:
                raise TranslationError("Unhandled projectionCentreFlag")

            # Always load PolarStereographic - never Stereographic.
            #  Stereographic is a CF/Iris concept and not something described
            #  in GRIB.
            # Note: I think the grib api defaults LaDInDegrees to 60 for grib1.
            self.extra_keys["_coord_system"] = coord_systems.PolarStereographic(
                pole_lat,
                self.orientationOfTheGridInDegrees,
                0,
                0,
                self.LaDInDegrees,
                ellipsoid=geoid,
            )

        elif gridType == "lambert":
            self.extra_keys["_x_coord_name"] = "projection_x_coordinate"
            self.extra_keys["_y_coord_name"] = "projection_y_coordinate"

            flag_name = "projectionCenterFlag"

            if getattr(self, flag_name) == 0:
                pole_lat = 90
            elif getattr(self, flag_name) == 1:
                pole_lat = -90
            else:
                raise TranslationError("Unhandled projectionCentreFlag")

            LambertConformal = coord_systems.LambertConformal
            self.extra_keys["_coord_system"] = LambertConformal(
                self.LaDInDegrees,
                self.LoVInDegrees,
                0,
                0,
                secant_latitudes=(self.Latin1InDegrees, self.Latin2InDegrees),
                ellipsoid=geoid,
            )
        else:
            raise TranslationError("unhandled grid type: {}".format(gridType))

        if gridType in ["regular_ll", "rotated_ll"]:
            self._regular_longitude_common()
            j_step = self.jDirectionIncrementInDegrees
            if not self.jScansPositively:
                j_step = -j_step
            self._y_points = (
                np.arange(self.Nj, dtype=np.float64) * j_step
                + self.latitudeOfFirstGridPointInDegrees
            )

        elif gridType in ["regular_gg"]:
            # longitude coordinate is straight-forward
            self._regular_longitude_common()
            # get the distinct latitudes, and make sure they are sorted
            # (south-to-north) and then put them in the right direction
            # depending on the scan direction
            latitude_points = eccodes.codes_get_double_array(
                self.grib_message, "distinctLatitudes"
            ).astype(np.float64)
            latitude_points.sort()
            if not self.jScansPositively:
                # we require latitudes north-to-south
                self._y_points = latitude_points[::-1]
            else:
                self._y_points = latitude_points

        elif gridType in ["polar_stereographic", "lambert"]:
            # convert the starting latlon into meters
            cartopy_crs = self.extra_keys["_coord_system"].as_cartopy_crs()
            x1, y1 = cartopy_crs.transform_point(
                self.longitudeOfFirstGridPointInDegrees,
                self.latitudeOfFirstGridPointInDegrees,
                ccrs.Geodetic(),
            )

            if not np.all(np.isfinite([x1, y1])):
                raise TranslationError(
                    "Could not determine the first latitude"
                    " and/or longitude grid point."
                )

            self._x_points = x1 + self.DxInMetres * np.arange(self.Nx, dtype=np.float64)
            self._y_points = y1 + self.DyInMetres * np.arange(self.Ny, dtype=np.float64)

        elif gridType in ["reduced_ll", "reduced_gg"]:
            self._x_points = self.longitudes
            self._y_points = self.latitudes

        else:
            raise TranslationError("unhandled grid type")

    def _regular_longitude_common(self):
        """Define a regular longitude dimension."""
        i_step = self.iDirectionIncrementInDegrees
        if self.iScansNegatively:
            i_step = -i_step
        self._x_points = (
            np.arange(self.Ni, dtype=np.float64) * i_step
            + self.longitudeOfFirstGridPointInDegrees
        )
        if "longitude" in self.extra_keys["_x_coord_name"] and self.Ni > 1:
            if _longitude_is_cyclic(self._x_points):
                self.extra_keys["_x_circular"] = True

    def _get_processing_done(self):
        """Determine the type of processing that was done on the data."""

        processingDone = "unknown"
        timeRangeIndicator = self.timeRangeIndicator
        default = "time _grib1_process_unknown_%i" % timeRangeIndicator
        processingDone = TIME_RANGE_INDICATORS.get(timeRangeIndicator, default)

        return processingDone

    def _get_verification_date(self):
        reference_date_time = self._referenceDateTime

        # calculate start time
        time_range_indicator = self.timeRangeIndicator
        P1 = self.P1
        P2 = self.P2
        if time_range_indicator == 0:
            # Forecast product valid at reference time + P1 P1>0),
            # or Uninitialized analysis product for reference time (P1=0).
            # Or Image product for reference time (P1=0)
            time_diff = P1
        elif time_range_indicator == 1:
            # Initialized analysis product for reference time (P1=0).
            time_diff = P1
        elif time_range_indicator == 2:
            # Product with a valid time ranging between reference time + P1
            # and reference time + P2
            time_diff = (P1 + P2) * 0.5
        elif time_range_indicator == 3:
            # Average(reference time + P1 to reference time + P2)
            time_diff = (P1 + P2) * 0.5
        elif time_range_indicator == 4:
            # Accumulation (reference time + P1 to reference time + P2)
            # product considered valid at reference time + P2
            time_diff = P2
        elif time_range_indicator == 5:
            # Difference(reference time + P2 minus reference time + P1)
            # product considered valid at reference time + P2
            time_diff = P2
        elif time_range_indicator == 10:
            # P1 occupies octets 19 and 20; product valid at
            # reference time + P1
            time_diff = P1 * 256 + P2
        elif time_range_indicator == 51:
            # Climatological Mean Value: multiple year averages of
            # quantities which are themselves means over some period of
            # time (P2) less than a year. The reference time (R) indicates
            # the date and time of the start of a period of time, given by
            # R to R + P2, over which a mean is formed; N indicates the number
            # of such period-means that are averaged together to form the
            # climatological value, assuming that the N period-mean fields
            # are separated by one year. The reference time indicates the
            # start of the N-year climatology. N is given in octets 22-23
            # of the PDS. If P1 = 0 then the data averaged in the basic
            # interval P2 are assumed to be continuous, i.e., all available
            # data are simply averaged together. If P1 = 1 (the units of
            # time - octet 18, code table 4 - are not relevant here) then
            # the data averaged together in the basic interval P2 are valid
            # only at the time (hour, minute) given in the reference time,
            # for all the days included in the P2 period. The units of P2
            # are given by the contents of octet 18 and Table 4.
            raise TranslationError(
                "unhandled grib1 timeRangeIndicator = 51 (avg of avgs)"
            )
        elif time_range_indicator == 113:
            # Average of N forecasts (or initialized analyses); each
            # product has forecast period of P1 (P1=0 for initialized
            # analyses); products have reference times at intervals of P2,
            # beginning at the given reference time.
            time_diff = P1
        elif time_range_indicator == 114:
            # Accumulation of N forecasts (or initialized analyses); each
            # product has forecast period of P1 (P1=0 for initialized
            # analyses); products have reference times at intervals of P2,
            # beginning at the given reference time.
            time_diff = P1
        elif time_range_indicator == 115:
            # Average of N forecasts, all with the same reference time;
            # the first has a forecast period of P1, the remaining
            # forecasts follow at intervals of P2.
            time_diff = P1
        elif time_range_indicator == 116:
            # Accumulation of N forecasts, all with the same reference
            # time; the first has a forecast period of P1, the remaining
            # follow at intervals of P2.
            time_diff = P1
        elif time_range_indicator == 117:
            # Average of N forecasts, the first has a period of P1, the
            # subsequent ones have forecast periods reduced from the
            # previous one by an interval of P2; the reference time for
            # the first is given in octets 13-17, the subsequent ones
            # have reference times increased from the previous one by
            # an interval of P2. Thus all the forecasts have the same
            # valid time, given by the initial reference time + P1.
            time_diff = P1
        elif time_range_indicator == 118:
            # Temporal variance, or covariance, of N initialized analyses;
            # each product has forecast period P1=0; products have
            # reference times at intervals of P2, beginning at the given
            # reference time.
            time_diff = P1
        elif time_range_indicator == 123:
            # Average of N uninitialized analyses, starting at the
            # reference time, at intervals of P2.
            time_diff = P1
        elif time_range_indicator == 124:
            # Accumulation of N uninitialized analyses, starting at
            # the reference time, at intervals of P2.
            time_diff = P1
        else:
            raise TranslationError(
                "unhandled grib1 timeRangeIndicator = %i" % time_range_indicator
            )

        # Get the timeunit interval.
        interval_secs = self._timeunit_seconds()
        # Multiply by start-offset and convert to a timedelta.
        #     NOTE: a 'float' conversion is required here, as time_diff may be
        #     a numpy scalar, which timedelta will not accept.
        interval_delta = datetime.timedelta(seconds=float(time_diff * interval_secs))
        # Return validity_time = (reference_time + start_offset*time_unit).
        return reference_date_time + interval_delta

    @property
    def bmdi(self):
        # Not sure of any cases where GRIB provides a fill value.
        # Default for fill value is None.
        return None

    def core_data(self):
        try:
            data = self._data
        except AttributeError:
            data = self.data
        return data

    def phenomenon_points(self, time_unit):
        """Return the phenomenon time points.

        As offsets from the epoch time reference, measured in appropriate time units.

        """
        time_reference = "%s since epoch" % time_unit
        return float(
            cf_units.date2num(
                self._phenomenonDateTime, time_reference, cf_units.CALENDAR_GREGORIAN
            )
        )

    def phenomenon_bounds(self, time_unit):
        """Return the phenomenon time bounds.

        As offsets from the epoch time reference, measured in appropriate time units.

        """
        # TODO #576 Investigate when it's valid to get phenomenon_bounds
        time_reference = "%s since epoch" % time_unit
        unit = cf_units.Unit(time_reference, cf_units.CALENDAR_GREGORIAN)
        return [
            float(unit.date2num(self._periodStartDateTime)),
            float(unit.date2num(self._periodEndDateTime)),
        ]


def _longitude_is_cyclic(points):
    """Work out if a set of longitude points is cyclic."""
    # Is the gap from end to start smaller, or about equal to the max step?
    gap = 360.0 - abs(points[-1] - points[0])
    max_step = abs(np.diff(points)).max()
    cyclic = False
    if gap <= max_step:
        cyclic = True
    else:
        delta = 0.001
        if abs(1.0 - gap / max_step) < delta:
            cyclic = True
    return cyclic


def _message_values(grib_message, shape):
    eccodes.codes_set_double(grib_message, "missingValue", np.nan)
    data = eccodes.codes_get_double_array(grib_message, "values")
    data = data.reshape(shape)

    # Handle missing values in a sensible way.
    mask = np.isnan(data)
    if mask.any():
        data = ma.array(data, mask=mask, fill_value=np.nan)
    return data


def _load_generate(filename):
    messages = GribMessage.messages_from_filename(filename)
    for message in messages:
        editionNumber = message.sections[0]["editionNumber"]
        if editionNumber == 1:
            has_bitmap = 3 in message.sections
            message_id = message._raw_message._message_id
            grib_fh = message._file_ref.open_file
            message = GribWrapper(message_id, grib_fh=grib_fh, has_bitmap=has_bitmap)
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
