# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Grib save implementation.

:mod:`iris_grib._save_rules` is a private module with no public API.
It is invoked from :meth:`iris_grib.save_grib2`.

"""

import warnings

import cf_units
import gribapi
from gribapi import GRIB_MISSING_LONG
import numpy as np
import numpy.ma as ma

import iris
from iris.aux_factory import HybridHeightFactory, HybridPressureFactory
from iris.coord_systems import (GeogCS, RotatedGeogCS, Mercator,
                                TransverseMercator, LambertConformal)
from iris.exceptions import TranslationError


from ._iris_mercator_support import confirm_extended_mercator_supported
from . import grib_phenom_translation as gptx
from ._load_convert import (_STATISTIC_TYPE_NAMES, _TIME_RANGE_UNITS,
                            _SPATIAL_PROCESSING_TYPES)
from .grib_phenom_translation import GRIBCode
from iris.util import is_regular, regular_step


# Invert code tables from :mod:`iris_grib._load_convert`.
_STATISTIC_TYPE_NAMES = {val: key for key, val in
                         _STATISTIC_TYPE_NAMES.items()}
_TIME_RANGE_UNITS = {val: key for key, val in _TIME_RANGE_UNITS.items()}


def fixup_float32_as_int32(value):
    """
    Workaround for use when the ECMWF GRIB API treats an IEEE 32-bit
    floating-point value as a signed, 4-byte integer.

    Returns the integer value which will result in the on-disk
    representation corresponding to the IEEE 32-bit floating-point
    value.

    """
    value_as_float32 = np.array(value, dtype='f4')
    value_as_uint32 = value_as_float32.view(dtype='u4')
    if value_as_uint32 >= 0x80000000:
        # Convert from two's-complement to sign-and-magnitude.
        # NB. Because of the silly representation of negative
        # integers in GRIB2, there is no value we can pass to
        # grib_set that will result in the bit pattern 0x80000000.
        # But since that bit pattern corresponds to a floating
        # point value of negative-zero, we can safely treat it as
        # positive-zero instead.
        value_as_grib_int = 0x80000000 - int(value_as_uint32)
    else:
        value_as_grib_int = int(value_as_uint32)
    return value_as_grib_int


def fixup_int32_as_uint32(value):
    """
    Workaround for use when the ECMWF GRIB API treats a signed, 4-byte
    integer value as an unsigned, 4-byte integer.

    Returns the unsigned integer value which will result in the on-disk
    representation corresponding to the signed, 4-byte integer value.

    """
    value = int(value)
    if -0x7fffffff <= value <= 0x7fffffff:
        if value < 0:
            # Convert from two's-complement to sign-and-magnitude.
            value = 0x80000000 - value
    else:
        msg = '{} out of range -2147483647 to 2147483647.'.format(value)
        raise ValueError(msg)
    return value


def ensure_set_int32_value(grib, key, value):
    """
    Ensure the workaround function :func:`fixup_int32_as_uint32` is applied as
    necessary to problem keys.

    """
    try:
        gribapi.grib_set(grib, key, value)
    except gribapi.GribInternalError:
        value = fixup_int32_as_uint32(value)
        gribapi.grib_set(grib, key, value)


###############################################################################
#
# Constants
#
###############################################################################

# Reference Flag Table 3.3
_RESOLUTION_AND_COMPONENTS_GRID_WINDS_BIT = 3  # NB "bit5", from MSB=1.

# Reference Regulation 92.1.6
_DEFAULT_DEGREES_UNITS = 1.0e-6


###############################################################################
#
# Identification Section 1
#
###############################################################################


def centre(cube, grib):
    # TODO: read centre from cube
    gribapi.grib_set_long(grib, "centre", 74)  # UKMO
    gribapi.grib_set_long(grib, "subCentre", 0)  # exeter is not in the spec


def reference_time(cube, grib):
    # Set the reference time.
    # (analysis, forecast start, verify time, obs time, etc)
    try:
        fp_coord = cube.coord("forecast_period")
    except iris.exceptions.CoordinateNotFoundError:
        fp_coord = None

    if fp_coord is not None:
        rt, rt_meaning, _, _ = _non_missing_forecast_period(cube)
    else:
        rt, rt_meaning, _, _ = _missing_forecast_period(cube)

    gribapi.grib_set_long(grib, "significanceOfReferenceTime", rt_meaning)
    gribapi.grib_set_long(
        grib, "dataDate", "%04d%02d%02d" % (rt.year, rt.month, rt.day))
    gribapi.grib_set_long(
        grib, "dataTime", "%02d%02d" % (rt.hour, rt.minute))

    # TODO: Set the calendar, when we find out what happened to the proposal!
    # http://tinyurl.com/oefqgv6
    # I was sure it was approved for pre-operational use but it's not there.


def identification(cube, grib):
    centre(cube, grib)
    reference_time(cube, grib)

    # operational product, operational test, research product, etc
    # (missing for now)
    gribapi.grib_set_long(grib, "productionStatusOfProcessedData", 255)

    # Code table 1.4
    # analysis, forecast, processed satellite, processed radar,
    if cube.coords('realization'):
        # assume realization will always have 1 and only 1 point
        # as cubes saving to GRIB2 a 2D horizontal slices
        if cube.coord('realization').points[0] != 0:
            gribapi.grib_set_long(grib, "typeOfProcessedData", 4)
        else:
            gribapi.grib_set_long(grib, "typeOfProcessedData", 3)
    else:
        gribapi.grib_set_long(grib, "typeOfProcessedData", 2)


###############################################################################
#
# Grid Definition Section 3
#
###############################################################################


def shape_of_the_earth(cube, grib):
    # assume latlon
    cs = cube.coord(dimensions=[0]).coord_system

    # Initially set shape_of_earth keys to missing (255 for byte).
    gribapi.grib_set_long(grib, "scaleFactorOfRadiusOfSphericalEarth", 255)
    gribapi.grib_set_long(grib, "scaledValueOfRadiusOfSphericalEarth",
                          GRIB_MISSING_LONG)
    gribapi.grib_set_long(grib, "scaleFactorOfEarthMajorAxis", 255)
    gribapi.grib_set_long(grib, "scaledValueOfEarthMajorAxis",
                          GRIB_MISSING_LONG)
    gribapi.grib_set_long(grib, "scaleFactorOfEarthMinorAxis", 255)
    gribapi.grib_set_long(grib, "scaledValueOfEarthMinorAxis",
                          GRIB_MISSING_LONG)

    if isinstance(cs, GeogCS):
        ellipsoid = cs
    else:
        ellipsoid = cs.ellipsoid
        if ellipsoid is None:
            msg = "Could not determine shape of the earth from coord system "\
                  "of horizontal grid."
            raise TranslationError(msg)

    # Spherical earth.
    if ellipsoid.inverse_flattening == 0.0:
        gribapi.grib_set_long(grib, "shapeOfTheEarth", 1)
        gribapi.grib_set_long(grib, "scaleFactorOfRadiusOfSphericalEarth", 0)
        gribapi.grib_set_long(grib, "scaledValueOfRadiusOfSphericalEarth",
                              ellipsoid.semi_major_axis)
        gribapi.grib_set_long(grib, "scaleFactorOfEarthMajorAxis", 0)
        gribapi.grib_set_long(grib, "scaledValueOfEarthMajorAxis", 0)
        gribapi.grib_set_long(grib, "scaleFactorOfEarthMinorAxis", 0)
        gribapi.grib_set_long(grib, "scaledValueOfEarthMinorAxis", 0)
    # Oblate spheroid earth.
    else:
        gribapi.grib_set_long(grib, "shapeOfTheEarth", 7)
        gribapi.grib_set_long(grib, "scaleFactorOfEarthMajorAxis", 0)
        gribapi.grib_set_long(grib, "scaledValueOfEarthMajorAxis",
                              ellipsoid.semi_major_axis)
        gribapi.grib_set_long(grib, "scaleFactorOfEarthMinorAxis", 0)
        gribapi.grib_set_long(grib, "scaledValueOfEarthMinorAxis",
                              ellipsoid.semi_minor_axis)


def grid_dims(x_coord, y_coord, grib, x_str, y_str):
    gribapi.grib_set_long(grib, x_str, x_coord.shape[0])
    gribapi.grib_set_long(grib, y_str, y_coord.shape[0])


def latlon_first_last(x_coord, y_coord, grib):
    if x_coord.has_bounds() or y_coord.has_bounds():
        warnings.warn("Ignoring xy bounds")

# XXX Pending #1125
#    gribapi.grib_set_double(grib, "latitudeOfFirstGridPointInDegrees",
#                            float(y_coord.points[0]))
#    gribapi.grib_set_double(grib, "latitudeOfLastGridPointInDegrees",
#                            float(y_coord.points[-1]))
#    gribapi.grib_set_double(grib, "longitudeOfFirstGridPointInDegrees",
#                            float(x_coord.points[0]))
#    gribapi.grib_set_double(grib, "longitudeOfLastGridPointInDegrees",
#                            float(x_coord.points[-1]))
# WORKAROUND
    gribapi.grib_set_long(grib, "latitudeOfFirstGridPoint",
                          int(y_coord.points[0]*1000000))
    gribapi.grib_set_long(grib, "latitudeOfLastGridPoint",
                          int(y_coord.points[-1]*1000000))
    gribapi.grib_set_long(grib, "longitudeOfFirstGridPoint",
                          int((x_coord.points[0] % 360)*1000000))
    gribapi.grib_set_long(grib, "longitudeOfLastGridPoint",
                          int((x_coord.points[-1] % 360)*1000000))


def dx_dy(x_coord, y_coord, grib):
    x_step = regular_step(x_coord)
    y_step = regular_step(y_coord)
    # Set x and y step.  For degrees, this is encoded as an integer:
    # 1 * 10^6 * floating point value.
    # WMO Manual on Codes regulation 92.1.6
    if x_coord.units == 'degrees':
        gribapi.grib_set(grib, "iDirectionIncrement",
                         round(1e6 * float(abs(x_step))))
    else:
        raise ValueError('X coordinate must be in degrees, not {}'
                         '.'.format(x_coord.units))
    if y_coord.units == 'degrees':
        gribapi.grib_set(grib, "jDirectionIncrement",
                         round(1e6 * float(abs(y_step))))
    else:
        raise ValueError('Y coordinate must be in degrees, not {}'
                         '.'.format(y_coord.units))


def scanning_mode_flags(x_coord, y_coord, grib):
    gribapi.grib_set_long(grib, "iScansPositively",
                          int(x_coord.points[1] - x_coord.points[0] > 0))
    gribapi.grib_set_long(grib, "jScansPositively",
                          int(y_coord.points[1] - y_coord.points[0] > 0))


def horizontal_grid_common(cube, grib, xy=False):
    nx_str, ny_str = ("Nx", "Ny") if xy else ("Ni", "Nj")
    # Grib encoding of the sequences of X and Y points.
    y_coord = cube.coord(dimensions=[0])
    x_coord = cube.coord(dimensions=[1])
    shape_of_the_earth(cube, grib)
    grid_dims(x_coord, y_coord, grib, nx_str, ny_str)
    scanning_mode_flags(x_coord, y_coord, grib)


def latlon_points_regular(cube, grib):
    y_coord = cube.coord(dimensions=[0])
    x_coord = cube.coord(dimensions=[1])
    latlon_first_last(x_coord, y_coord, grib)
    dx_dy(x_coord, y_coord, grib)


def latlon_points_irregular(cube, grib):
    y_coord = cube.coord(dimensions=[0])
    x_coord = cube.coord(dimensions=[1])

    # Distinguish between true-north and grid-oriented vectors.
    is_grid_wind = cube.name() in ('x_wind', 'y_wind', 'grid_eastward_wind',
                                   'grid_northward_wind')
    # Encode in bit "5" of 'resolutionAndComponentFlags' (other bits unused).
    component_flags = 0
    if is_grid_wind:
        component_flags |= 2 ** _RESOLUTION_AND_COMPONENTS_GRID_WINDS_BIT
    gribapi.grib_set(grib, 'resolutionAndComponentFlags', component_flags)

    # Record the  X and Y coordinate values.
    # NOTE: there is currently a bug in the gribapi which means that the size
    # of the longitudes array does not equal 'Nj', as it should.
    # See : https://software.ecmwf.int/issues/browse/SUP-1096
    # So, this only works at present if the x and y dimensions are **equal**.
    lon_values = x_coord.points / _DEFAULT_DEGREES_UNITS
    lat_values = y_coord.points / _DEFAULT_DEGREES_UNITS
    gribapi.grib_set_array(grib, 'longitudes',
                           np.array(np.round(lon_values), dtype=np.int64))
    gribapi.grib_set_array(grib, 'latitudes',
                           np.array(np.round(lat_values), dtype=np.int64))


def rotated_pole(cube, grib):
    # Grib encoding of a rotated pole coordinate system.
    cs = cube.coord(dimensions=[0]).coord_system

    if cs.north_pole_grid_longitude != 0.0:
        raise TranslationError(
            'Grib save does not yet support Rotated-pole coordinates with '
            'a rotated prime meridian.')
# XXX Pending #1125
#    gribapi.grib_set_double(grib, "latitudeOfSouthernPoleInDegrees",
#                            float(cs.n_pole.latitude))
#    gribapi.grib_set_double(grib, "longitudeOfSouthernPoleInDegrees",
#                            float(cs.n_pole.longitude))
#    gribapi.grib_set_double(grib, "angleOfRotationInDegrees", 0)
# WORKAROUND
    latitude = cs.grid_north_pole_latitude / _DEFAULT_DEGREES_UNITS
    longitude = (((cs.grid_north_pole_longitude + 180) % 360) /
                 _DEFAULT_DEGREES_UNITS)
    gribapi.grib_set(grib, "latitudeOfSouthernPole", - int(round(latitude)))
    gribapi.grib_set(grib, "longitudeOfSouthernPole", int(round(longitude)))
    gribapi.grib_set(grib, "angleOfRotation", 0)


def points_in_unit(coord, unit):
    points = coord.units.convert(coord.points, unit)
    points = np.around(points).astype(int)
    return points


def step(points, atol):
    diffs = points[1:] - points[:-1]
    mean_diff = np.mean(diffs).astype(points.dtype)
    if not np.allclose(diffs, mean_diff, atol=atol):
        raise ValueError()
    return int(mean_diff)


def grid_definition_template_0(cube, grib):
    """
    Set keys within the provided grib message based on
    Grid Definition Template 3.0.

    Template 3.0 is used to represent "latitude/longitude (or equidistant
    cylindrical, or Plate Carree)".
    The coordinates are regularly spaced, true latitudes and longitudes.

    """
    # Constant resolution, aka 'regular' true lat-lon grid.
    gribapi.grib_set_long(grib, "gridDefinitionTemplateNumber", 0)
    horizontal_grid_common(cube, grib)
    latlon_points_regular(cube, grib)


def grid_definition_template_1(cube, grib):
    """
    Set keys within the provided grib message based on
    Grid Definition Template 3.1.

    Template 3.1 is used to represent "rotated latitude/longitude (or
    equidistant cylindrical, or Plate Carree)".
    The coordinates are regularly spaced, rotated latitudes and longitudes.

    """
    # Constant resolution, aka 'regular' rotated lat-lon grid.
    gribapi.grib_set_long(grib, "gridDefinitionTemplateNumber", 1)

    # Record details of the rotated coordinate system.
    rotated_pole(cube, grib)

    # Encode the lat/lon points.
    horizontal_grid_common(cube, grib)
    latlon_points_regular(cube, grib)


def grid_definition_template_4(cube, grib):
    """
    Set keys within the provided grib message based on
    Grid Definition Template 3.4.

    Template 3.4 is used to represent "variable resolution latitude/longitude".
    The coordinates are irregularly spaced latitudes and longitudes.

    """
    # XXX: will we need to set `Ni` and `Nj`?
    gribapi.grib_set(grib, "gridDefinitionTemplateNumber", 4)
    horizontal_grid_common(cube, grib)
    latlon_points_irregular(cube, grib)


def grid_definition_template_5(cube, grib):
    """
    Set keys within the provided grib message based on
    Grid Definition Template 3.5.

    Template 3.5 is used to represent "variable resolution rotated
    latitude/longitude".
    The coordinates are irregularly spaced, rotated latitudes and longitudes.

    """
    # NOTE: we must set Ni=Nj=1 before establishing the template.
    # Without this, setting "gridDefinitionTemplateNumber" = 5 causes an
    # immediate error.
    # See: https://software.ecmwf.int/issues/browse/SUP-1095
    # This is acceptable, as the subsequent call to 'horizontal_grid_common'
    # will set these to the correct horizontal dimensions
    # (by calling 'grid_dims').
    gribapi.grib_set(grib, "Ni", 1)
    gribapi.grib_set(grib, "Nj", 1)
    gribapi.grib_set(grib, "gridDefinitionTemplateNumber", 5)

    # Record details of the rotated coordinate system.
    rotated_pole(cube, grib)
    # Encode the lat/lon points.
    horizontal_grid_common(cube, grib)
    latlon_points_irregular(cube, grib)


def grid_definition_template_10(cube, grib):
    """
    Set keys within the provided grib message based on
    Grid Definition Template 3.10.

    Template 3.10 is used to represent a Mercator grid.

    """
    gribapi.grib_set(grib, "gridDefinitionTemplateNumber", 10)

    # Retrieve some information from the cube.
    y_coord = cube.coord(dimensions=[0])
    x_coord = cube.coord(dimensions=[1])
    cs = y_coord.coord_system

    # Normalise the coordinate values to millimetres - the resolution
    # used in the GRIB message.
    y_mm = points_in_unit(y_coord, 'mm')
    x_mm = points_in_unit(x_coord, 'mm')

    # Encode the horizontal points.

    # NB. Since we're already in millimetres, our tolerance for
    # discrepancy in the differences is 1.
    try:
        x_step = step(x_mm, atol=1)
        y_step = step(y_mm, atol=1)
    except ValueError:
        msg = 'Irregular coordinates not supported for Mercator.'
        raise TranslationError(msg)

    gribapi.grib_set(grib, 'Di', abs(x_step))
    gribapi.grib_set(grib, 'Dj', abs(y_step))

    horizontal_grid_common(cube, grib)

    # Transform first and last points into geographic CS.
    geog = cs.ellipsoid if cs.ellipsoid is not None else GeogCS(1)
    first_x, first_y, = geog.as_cartopy_crs().transform_point(
        x_coord.points[0],
        y_coord.points[0],
        cs.as_cartopy_crs())
    last_x, last_y = geog.as_cartopy_crs().transform_point(
        x_coord.points[-1],
        y_coord.points[-1],
        cs.as_cartopy_crs())
    first_x = first_x % 360
    last_x = last_x % 360

    gribapi.grib_set(grib, "latitudeOfFirstGridPoint",
                     int(np.round(first_y / _DEFAULT_DEGREES_UNITS)))
    gribapi.grib_set(grib, "longitudeOfFirstGridPoint",
                     int(np.round(first_x / _DEFAULT_DEGREES_UNITS)))
    gribapi.grib_set(grib, "latitudeOfLastGridPoint",
                     int(np.round(last_y / _DEFAULT_DEGREES_UNITS)))
    gribapi.grib_set(grib, "longitudeOfLastGridPoint",
                     int(np.round(last_x / _DEFAULT_DEGREES_UNITS)))

    # Check and raise a more intelligible error, if the Iris version is too old
    # to support the Mercator 'standard_parallel' property.
    confirm_extended_mercator_supported()
    # Encode the latitude at which the projection intersects the Earth.
    gribapi.grib_set(grib, 'LaD',
                     cs.standard_parallel / _DEFAULT_DEGREES_UNITS)

    # Encode resolution and component flags
    gribapi.grib_set(grib, 'resolutionAndComponentFlags',
                     0x1 << _RESOLUTION_AND_COMPONENTS_GRID_WINDS_BIT)


def grid_definition_template_12(cube, grib):
    """
    Set keys within the provided grib message based on
    Grid Definition Template 3.12.

    Template 3.12 is used to represent a Transverse Mercator grid.

    """
    gribapi.grib_set(grib, "gridDefinitionTemplateNumber", 12)

    # Retrieve some information from the cube.
    y_coord = cube.coord(dimensions=[0])
    x_coord = cube.coord(dimensions=[1])
    cs = y_coord.coord_system

    # Normalise the coordinate values to centimetres - the resolution
    # used in the GRIB message.
    y_cm = points_in_unit(y_coord, 'cm')
    x_cm = points_in_unit(x_coord, 'cm')

    # Set some keys specific to GDT12.
    # Encode the horizontal points.

    # NB. Since we're already in centimetres, our tolerance for
    # discrepancy in the differences is 1.
    try:
        x_step = step(x_cm, atol=1)
        y_step = step(y_cm, atol=1)
    except ValueError:
        msg = ('Irregular coordinates not supported for Transverse '
               'Mercator.')
        raise TranslationError(msg)
    gribapi.grib_set(grib, 'Di', abs(x_step))
    gribapi.grib_set(grib, 'Dj', abs(y_step))
    horizontal_grid_common(cube, grib)

    # GRIBAPI expects unsigned ints in X1, X2, Y1, Y2 but it should accept
    # signed ints, so work around this.
    # See https://software.ecmwf.int/issues/browse/SUP-1101
    ensure_set_int32_value(grib, 'Y1', int(y_cm[0]))
    ensure_set_int32_value(grib, 'Y2', int(y_cm[-1]))
    ensure_set_int32_value(grib, 'X1', int(x_cm[0]))
    ensure_set_int32_value(grib, 'X2', int(x_cm[-1]))

    # Lat and lon of reference point are measured in millionths of a degree.
    gribapi.grib_set(grib, "latitudeOfReferencePoint",
                     cs.latitude_of_projection_origin / _DEFAULT_DEGREES_UNITS)
    gribapi.grib_set(grib, "longitudeOfReferencePoint",
                     cs.longitude_of_central_meridian / _DEFAULT_DEGREES_UNITS)

    # Convert a value in metres into the closest integer number of
    # centimetres.
    def m_to_cm(value):
        return int(round(value * 100))

    # False easting and false northing are measured in units of (10^-2)m.
    gribapi.grib_set(grib, 'XR', m_to_cm(cs.false_easting))
    gribapi.grib_set(grib, 'YR', m_to_cm(cs.false_northing))

    # GRIBAPI expects a signed int for scaleFactorAtReferencePoint
    # but it should accept a float, so work around this.
    # See https://software.ecmwf.int/issues/browse/SUP-1100
    value = cs.scale_factor_at_central_meridian
    key_type = gribapi.grib_get_native_type(grib,
                                            "scaleFactorAtReferencePoint")
    if key_type is not float:
        value = fixup_float32_as_int32(value)
    gribapi.grib_set(grib, "scaleFactorAtReferencePoint", value)


def grid_definition_template_30(cube, grib):
    """
    Set keys within the provided grib message based on
    Grid Definition Template 3.30.

    Template 3.30 is used to represent a Lambert Conformal grid.

    """

    gribapi.grib_set(grib, "gridDefinitionTemplateNumber", 30)

    # Retrieve some information from the cube.
    y_coord = cube.coord(dimensions=[0])
    x_coord = cube.coord(dimensions=[1])
    cs = y_coord.coord_system

    # Normalise the coordinate values to millimetres - the resolution
    # used in the GRIB message.
    y_mm = points_in_unit(y_coord, 'mm')
    x_mm = points_in_unit(x_coord, 'mm')

    # Encode the horizontal points.

    # NB. Since we're already in millimetres, our tolerance for
    # discrepancy in the differences is 1.
    try:
        x_step = step(x_mm, atol=1)
        y_step = step(y_mm, atol=1)
    except ValueError:
        msg = ('Irregular coordinates not supported for Lambert '
               'Conformal.')
        raise TranslationError(msg)
    gribapi.grib_set(grib, 'Dx', abs(x_step))
    gribapi.grib_set(grib, 'Dy', abs(y_step))

    horizontal_grid_common(cube, grib, xy=True)

    # Transform first point into geographic CS
    geog = cs.ellipsoid if cs.ellipsoid is not None else GeogCS(1)
    first_x, first_y = geog.as_cartopy_crs().transform_point(
        x_coord.points[0],
        y_coord.points[0],
        cs.as_cartopy_crs())
    first_x = first_x % 360
    central_lon = cs.central_lon % 360

    gribapi.grib_set(grib, "latitudeOfFirstGridPoint",
                     int(np.round(first_y / _DEFAULT_DEGREES_UNITS)))
    gribapi.grib_set(grib, "longitudeOfFirstGridPoint",
                     int(np.round(first_x / _DEFAULT_DEGREES_UNITS)))
    gribapi.grib_set(grib, "LaD", cs.central_lat / _DEFAULT_DEGREES_UNITS)
    gribapi.grib_set(grib, "LoV", central_lon / _DEFAULT_DEGREES_UNITS)
    latin1, latin2 = cs.secant_latitudes
    gribapi.grib_set(grib, "Latin1", latin1 / _DEFAULT_DEGREES_UNITS)
    gribapi.grib_set(grib, "Latin2", latin2 / _DEFAULT_DEGREES_UNITS)
    gribapi.grib_set(grib, 'resolutionAndComponentFlags',
                     0x1 << _RESOLUTION_AND_COMPONENTS_GRID_WINDS_BIT)

    # Which pole are the parallels closest to? That is the direction
    # that the cone converges.
    poliest_sec = latin1 if abs(latin1) > abs(latin2) else latin2
    centre_flag = 0x0 if poliest_sec > 0 else 0x1
    gribapi.grib_set(grib, 'projectionCentreFlag', centre_flag)
    gribapi.grib_set(grib, "latitudeOfSouthernPole", 0)
    gribapi.grib_set(grib, "longitudeOfSouthernPole", 0)


def grid_definition_section(cube, grib):
    """
    Set keys within the grid definition section of the provided grib message,
    based on the properties of the cube.

    """
    x_coord = cube.coord(dimensions=[1])
    y_coord = cube.coord(dimensions=[0])
    cs = x_coord.coord_system  # N.B. already checked same cs for x and y.
    regular_x_and_y = is_regular(x_coord) and is_regular(y_coord)

    if isinstance(cs, GeogCS):
        if regular_x_and_y:
            grid_definition_template_0(cube, grib)
        else:
            grid_definition_template_4(cube, grib)

    elif isinstance(cs, RotatedGeogCS):
        # Rotated coordinate system cases.
        # Choose between GDT 3.1 and 3.5 according to coordinate regularity.
        if regular_x_and_y:
            grid_definition_template_1(cube, grib)
        else:
            grid_definition_template_5(cube, grib)

    elif isinstance(cs, Mercator):
        # Mercator coordinate system (template 3.10)
        grid_definition_template_10(cube, grib)

    elif isinstance(cs, TransverseMercator):
        # Transverse Mercator coordinate system (template 3.12).
        grid_definition_template_12(cube, grib)

    elif isinstance(cs, LambertConformal):
        # Lambert Conformal coordinate system (template 3.30).
        grid_definition_template_30(cube, grib)
    else:
        name = cs.grid_mapping_name.replace('_', ' ').title()
        emsg = 'Grib saving is not supported for coordinate system {!r}'
        raise ValueError(emsg.format(name))


###############################################################################
#
# Product Definition Section 4
#
###############################################################################

def set_discipline_and_parameter(cube, grib):
    # Default values for parameter identity keys = effectively "MISSING".
    discipline, category, number = 255, 255, 255
    identity_found = False

    # First, see if we can find and interpret a 'GRIB_PARAM' attribute.
    attr = cube.attributes.get('GRIB_PARAM', None)
    if attr:
        try:
            # Convert to standard tuple-derived form.
            gc = GRIBCode(attr)
            if gc.edition == 2:
                discipline = gc.discipline
                category = gc.category
                number = gc.number
                identity_found = True
        except Exception:
            pass

    if not identity_found:
        # Else, translate a cube phenomenon, if possible.
        # NOTE: for now, can match by *either* standard_name or long_name.
        # This allows workarounds for data with no identified standard_name.
        grib2_info = gptx.cf_phenom_to_grib2_info(cube.standard_name,
                                                  cube.long_name)
        if grib2_info is not None:
            discipline = grib2_info.discipline
            category = grib2_info.category
            number = grib2_info.number
            identity_found = True

    if not identity_found:
        warnings.warn('Unable to determine Grib2 parameter code for cube.\n'
                      'discipline, parameterCategory and parameterNumber '
                      'have been set to "missing".')

    gribapi.grib_set(grib, "discipline", discipline)
    gribapi.grib_set(grib, "parameterCategory", category)
    gribapi.grib_set(grib, "parameterNumber", number)


def _non_missing_forecast_period(cube):
    # Calculate "model start time" to use as the reference time.
    fp_coord = cube.coord("forecast_period")

    # Convert fp and t to hours so we can subtract to calculate R.
    cf_fp_hrs = fp_coord.units.convert(fp_coord.points[0], 'hours')
    t_coord = cube.coord("time").copy()
    hours_since = cf_units.Unit("hours since epoch",
                                calendar=t_coord.units.calendar)
    t_coord.convert_units(hours_since)

    rt_num = t_coord.points[0] - cf_fp_hrs
    rt = hours_since.num2date(rt_num)
    rt_meaning = 1  # "start of forecast"

    # Forecast period
    if fp_coord.units == cf_units.Unit("hours"):
        grib_time_code = 1
    elif fp_coord.units == cf_units.Unit("minutes"):
        grib_time_code = 0
    elif fp_coord.units == cf_units.Unit("seconds"):
        grib_time_code = 13
    else:
        raise TranslationError(
            "Unexpected units for 'forecast_period' : %s" % fp_coord.units)

    if not t_coord.has_bounds():
        fp = fp_coord.points[0]
    else:
        if not fp_coord.has_bounds():
            raise TranslationError(
                "bounds on 'time' coordinate requires bounds on"
                " 'forecast_period'.")
        fp = fp_coord.bounds[0][0]

    if fp - int(fp):
        warnings.warn("forecast_period encoding problem: "
                      "scaling required.")
    fp = int(fp)

    return rt, rt_meaning, fp, grib_time_code


def _missing_forecast_period(cube):
    """
    Returns a reference time and significance code together with a forecast
    period and corresponding units type code.

    """
    t_coord = cube.coord("time")

    if cube.coords('forecast_reference_time'):
        # Make copies and convert them to common "hours since" units.
        hours_since = cf_units.Unit('hours since epoch',
                                    calendar=t_coord.units.calendar)
        frt_coord = cube.coord('forecast_reference_time').copy()
        frt_coord.convert_units(hours_since)
        t_coord = t_coord.copy()
        t_coord.convert_units(hours_since)
        # Extract values.
        t = t_coord.bounds[0, 0] if t_coord.has_bounds() else t_coord.points[0]
        frt = frt_coord.points[0]
        # Calculate GRIB parameters.
        rt = frt_coord.units.num2date(frt)
        rt_meaning = 1  # Forecast reference time.
        fp = t - frt
        integer_fp = int(fp)
        if integer_fp != fp:
            msg = 'Truncating floating point forecast period {} to ' \
                  'integer value {}'
            warnings.warn(msg.format(fp, integer_fp))
        fp = integer_fp
        fp_meaning = 1  # Hours
    else:
        # With no forecast period or forecast reference time set assume a
        # reference time significance of "Observation time" and set the
        # forecast period to 0h.
        t = t_coord.bounds[0, 0] if t_coord.has_bounds() else t_coord.points[0]
        rt = t_coord.units.num2date(t)
        rt_meaning = 3  # Observation time
        fp = 0
        fp_meaning = 1  # Hours

    return rt, rt_meaning, fp, fp_meaning


def set_forecast_time(cube, grib):
    """
    Set the forecast time keys based on the forecast_period coordinate. In
    the absence of a forecast_period and forecast_reference_time,
    the forecast time is set to zero.

    """
    try:
        fp_coord = cube.coord("forecast_period")
    except iris.exceptions.CoordinateNotFoundError:
        fp_coord = None

    if fp_coord is not None:
        _, _, fp, grib_time_code = _non_missing_forecast_period(cube)
    else:
        _, _, fp, grib_time_code = _missing_forecast_period(cube)

    gribapi.grib_set(grib, "indicatorOfUnitOfTimeRange", grib_time_code)
    gribapi.grib_set(grib, "forecastTime", fp)


def set_fixed_surfaces(cube, grib, full3d_cube=None):

    # Look for something we can export
    v_coord = grib_v_code = output_unit = None

    # Detect factories for hybrid vertical coordinates.
    hybrid_factories = [
        factory for factory in cube.aux_factories
        if isinstance(factory, (HybridHeightFactory, HybridPressureFactory))]
    if not hybrid_factories:
        hybrid_factory = None
    elif len(hybrid_factories) > 1:
        msg = 'Data contains >1 vertical coordinate factory : {}'
        raise ValueError(msg.format(hybrid_factories))
    else:
        factory = hybrid_factories[0]
        # Fetch the matching 'complete' factory from the *full* 3d cube, so we
        # have all the level information.
        hybrid_factory = full3d_cube.aux_factory(factory.name())

    # Handle various different styles of vertical coordinate.
    # hybrid height / pressure
    if hybrid_factory is not None:
        # N.B. in this case, there are additional operations, besides just
        # encoding v_coord : see below at end ..
        v_coord = cube.coord('model_level_number')
        output_unit = cf_units.Unit("1")
        if isinstance(hybrid_factory, HybridHeightFactory):
            grib_v_code = 118
        elif isinstance(hybrid_factory, HybridPressureFactory):
            grib_v_code = 119
        else:
            msg = 'Unrecognised factory type : {}'
            raise ValueError(msg.format(hybrid_factory))

    # pressure
    elif cube.coords("air_pressure") or cube.coords("pressure"):
        grib_v_code = 100
        output_unit = cf_units.Unit("Pa")
        v_coord = (cube.coords("air_pressure") or cube.coords("pressure"))[0]

    # altitude
    elif cube.coords("altitude"):
        grib_v_code = 102
        output_unit = cf_units.Unit("m")
        v_coord = cube.coord("altitude")

    # height
    elif cube.coords("height"):
        grib_v_code = 103
        output_unit = cf_units.Unit("m")
        v_coord = cube.coord("height")

    # depth
    elif cube.coords("depth"):
        grib_v_code = 106
        output_unit = cf_units.Unit('m')
        v_coord = cube.coord("depth")

    elif cube.coords("air_potential_temperature"):
        grib_v_code = 107
        output_unit = cf_units.Unit('K')
        v_coord = cube.coord("air_potential_temperature")

    # unknown / absent
    else:
        # check for *ANY* height coords at all...
        v_coords = cube.coords(axis='z')
        if v_coords:
            # There are vertical coordinate(s), but we don't understand them...
            v_coords_str = ' ,'.join(["'{}'".format(c.name())
                                      for c in v_coords])
            raise TranslationError(
                'The vertical-axis coordinate(s) ({}) '
                'are not recognised or handled.'.format(v_coords_str))

    # What did we find?
    if v_coord is None:
        # No vertical coordinate: record as 'surface' level (levelType=1).
        # NOTE: may *not* be truly correct, but seems to be common practice.
        # Still under investigation :
        # See https://github.com/SciTools/iris/issues/519
        gribapi.grib_set(grib, "typeOfFirstFixedSurface", 1)
        gribapi.grib_set(grib, "scaleFactorOfFirstFixedSurface", 0)
        gribapi.grib_set(grib, "scaledValueOfFirstFixedSurface", 0)
        # Set secondary surface = 'missing'.
        gribapi.grib_set(grib, "typeOfSecondFixedSurface", 255)
        gribapi.grib_set(grib, "scaleFactorOfSecondFixedSurface", 255)
        gribapi.grib_set(grib, "scaledValueOfSecondFixedSurface",
                         GRIB_MISSING_LONG)
    elif not v_coord.has_bounds():
        # No second surface
        output_v = v_coord.units.convert(v_coord.points[0], output_unit)
        if output_v - abs(output_v):
            warnings.warn("Vertical level encoding problem: scaling required.")
        output_v = int(round(output_v))

        gribapi.grib_set(grib, "typeOfFirstFixedSurface", grib_v_code)
        gribapi.grib_set(grib, "scaleFactorOfFirstFixedSurface", 0)
        gribapi.grib_set(grib, "scaledValueOfFirstFixedSurface", output_v)
        gribapi.grib_set(grib, "typeOfSecondFixedSurface", 255)
        gribapi.grib_set(grib, "scaleFactorOfSecondFixedSurface", 255)
        gribapi.grib_set(grib, "scaledValueOfSecondFixedSurface",
                         GRIB_MISSING_LONG)
    else:
        # bounded : set lower+upper surfaces
        output_v = v_coord.units.convert(v_coord.bounds[0], output_unit)
        if output_v[0] - abs(output_v[0]) or output_v[1] - abs(output_v[1]):
            warnings.warn("Vertical level encoding problem: scaling required.")
        gribapi.grib_set(grib, "typeOfFirstFixedSurface", grib_v_code)
        gribapi.grib_set(grib, "typeOfSecondFixedSurface", grib_v_code)
        gribapi.grib_set(grib, "scaleFactorOfFirstFixedSurface", 0)
        gribapi.grib_set(grib, "scaleFactorOfSecondFixedSurface", 0)
        gribapi.grib_set(grib, "scaledValueOfFirstFixedSurface",
                         int(round(output_v[0])))
        gribapi.grib_set(grib, "scaledValueOfSecondFixedSurface",
                         int(round(output_v[1])))

    if hybrid_factory is not None:
        # Need to record ALL the level coefficents in a 'PV' vector.
        level_delta_coord = hybrid_factory.delta
        sigma_coord = hybrid_factory.sigma
        model_levels = full3d_cube.coord('model_level_number').points
        # Just check these make some kind of sense (!)
        if model_levels.dtype.kind not in 'iu':
            msg = 'model_level_number is not an integer: dtype={}.'
            raise ValueError(msg.format(model_levels.dtype))
        if np.min(model_levels) < 1:
            msg = 'model_level_number must be > 0: mininum value = {}.'
            raise ValueError(msg.format(np.min(model_levels)))
        # Need to save enough levels for indexes up to  [max(model_levels)]
        n_levels = np.max(model_levels)
        max_valid_nlevels = 9999
        if n_levels > max_valid_nlevels:
            msg = ('model_level_number values are > {} : '
                   'maximum value = {}.')
            raise ValueError(msg.format(max_valid_nlevels, n_levels))
        # In sample data we have seen, there seems to be an extra missing data
        # value *before* each set of n-levels coefficients.
        # Note: values are indexed according to model_level_number,
        # I.E. sigma, delta = PV[i], PV[NV/2+i] : where i=1..n_levels
        n_coeffs = n_levels + 1
        coeffs_array = np.zeros(n_coeffs * 2, dtype=np.float32)
        for n_lev, height, sigma in zip(model_levels,
                                        level_delta_coord.points,
                                        sigma_coord.points):
            # Record all the level coefficients coming from the 'full' cube.
            # Note: if some model levels are missing, we must still have the
            # coeffs at the correct index according to the model_level_number
            # value, i.e. at [level] and [NV // 2 + level].
            # Thus, we can *not* paste the values in a block: each one needs to
            # go in the index corresponding to its 'model_level_number' value.
            coeffs_array[n_lev] = height
            coeffs_array[n_coeffs + n_lev] = sigma
        pv_values = [float(el) for el in coeffs_array]
        # eccodes does not support writing numpy.int64, cast to python int
        gribapi.grib_set(grib, "NV", int(n_coeffs * 2))
        gribapi.grib_set_array(grib, "pv", pv_values)


def set_time_range(time_coord, grib):
    """
    Set the time range keys in the specified message
    based on the bounds of the provided time coordinate.

    """
    if len(time_coord.points) != 1:
        msg = 'Expected length one time coordinate, got {} points'
        raise ValueError(msg.format(len(time_coord.points)))

    if time_coord.nbounds != 2:
        msg = 'Expected time coordinate with two bounds, got {} bounds'
        raise ValueError(msg.format(time_coord.nbounds))

    # Set type to hours and convert period to this unit.
    gribapi.grib_set(grib, "indicatorOfUnitForTimeRange",
                     _TIME_RANGE_UNITS['hours'])
    hours_since_units = cf_units.Unit('hours since epoch',
                                      calendar=time_coord.units.calendar)
    start_hours, end_hours = time_coord.units.convert(time_coord.bounds[0],
                                                      hours_since_units)
    # Cast from np.float to Python int. The lengthOfTimeRange key is a
    # 4 byte integer so we cast to highlight truncation of any floating
    # point value. The grib_api will do the cast from float to int, but it
    # cannot handle numpy floats.
    time_range_in_hours = end_hours - start_hours
    integer_hours = int(time_range_in_hours)
    if integer_hours != time_range_in_hours:
        msg = 'Truncating floating point lengthOfTimeRange {} to ' \
              'integer value {}'
        warnings.warn(msg.format(time_range_in_hours, integer_hours))
    gribapi.grib_set(grib, "lengthOfTimeRange", integer_hours)


def set_time_increment(cell_method, grib):
    """
    Set the time increment keys in the specified message
    based on the provided cell method.

    """
    # Type of time increment, e.g incrementing forecast period, incrementing
    # forecast reference time, etc. Set to missing, but we could use the
    # cell method coord to infer a value (see code table 4.11).
    gribapi.grib_set(grib, "typeOfTimeIncrement", 255)

    # Default values for the time increment value and units type.
    inc = 0
    units_type = 255
    # Attempt to determine time increment from cell method intervals string.
    intervals = cell_method.intervals
    if intervals is not None and len(intervals) == 1:
        interval, = intervals
        try:
            inc, units = interval.split()
            inc = float(inc)
            if units in ('hr', 'hour', 'hours'):
                units_type = _TIME_RANGE_UNITS['hours']
            else:
                raise ValueError('Unable to parse units of interval')
        except ValueError:
            # Problem interpreting the interval string.
            inc = 0
            units_type = 255
        else:
            # Cast to int as timeIncrement key is a 4 byte integer.
            integer_inc = int(inc)
            if integer_inc != inc:
                warnings.warn('Truncating floating point timeIncrement {} to '
                              'integer value {}'.format(inc, integer_inc))
            inc = integer_inc

    gribapi.grib_set(grib, "indicatorOfUnitForTimeIncrement", units_type)
    gribapi.grib_set(grib, "timeIncrement", inc)


def _cube_is_time_statistic(cube):
    """
    Test whether we can identify this cube as a statistic over time.

    We need to know whether our cube represents a time statistic. This is
    almost always captured in the cell methods. The exception is when a
    percentage statistic has been calculated (i.e. for PDT10). This is
    captured in a `percentage_over_time` scalar coord, which must be handled
    here too.

    """
    result = False
    stat_coord_name = 'percentile_over_time'
    cube_coord_names = [coord.name() for coord in cube.coords()]

    # Check our cube for time statistic indicators.
    has_percentile_statistic = stat_coord_name in cube_coord_names
    has_cell_methods = cube.cell_methods

    # Determine whether we have a time statistic.
    if has_percentile_statistic:
        result = True
    elif has_cell_methods:
        # Define accepted time names, including from coord_categorisations.
        recognised_time_names = ['time', 'year', 'month', 'day', 'weekday',
                                 'season']
        latest_coordnames = cube.cell_methods[-1].coord_names
        if len(latest_coordnames) != 1:
            result = False
        else:
            coord_name = latest_coordnames[0]
            result = coord_name in recognised_time_names
    else:
        result = False

    return result


def _spatial_statistic(cube):
    """
    Gather and return the spatial statistic of the cube if it is present.

    """
    spatial_cell_methods = [
        cell_method for cell_method in cube.cell_methods if 'area' in
        cell_method.coord_names]

    if len(spatial_cell_methods) > 1:
        raise ValueError("Cannot handle multiple 'area' cell methods")
    elif len(spatial_cell_methods[0].coord_names) > 1:
        raise ValueError("Cannot handle multiple coordinate names in "
                         "the spatial processing related cell method. "
                         "Expected ('area',), got {!r}".format
                         (spatial_cell_methods[0].coord_names))

    return spatial_cell_methods


def statistical_method_code(cell_method_name):
    """
    Decode cell_method string as statistic code integer.
    """
    statistic_code = _STATISTIC_TYPE_NAMES.get(cell_method_name, None)
    if statistic_code is None:
        msg = ('Product definition section 4 contains an unsupported '
               'statistical process type [{}] ')
        raise TranslationError(msg.format(statistic_code))

    return statistic_code


def get_spatial_process_code(spatial_processing_type):
    """
    Decode spatial_processing_type string as spatial process code integer.
    """
    spatial_processing_code = None

    for code, interp_params in _SPATIAL_PROCESSING_TYPES.items():
        if interp_params.interpolation_type == spatial_processing_type:
            spatial_processing_code = code
            break

    if spatial_processing_code is None:
        msg = ('Product definition section 4 contains an unsupported '
               'spatial processing or interpolation type: {} ')
        raise TranslationError(msg.format(spatial_processing_type))

    return spatial_processing_code


def set_ensemble(cube, grib):
    """
    Set keys in the provided grib based message relating to ensemble
    information.

    """
    if not (cube.coords('realization') and
            len(cube.coord('realization').points) == 1):
        raise ValueError("A cube 'realization' coordinate with one "
                         "point is required, but not present")
    gribapi.grib_set(grib, "perturbationNumber",
                     int(cube.coord('realization').points[0]))
    # no encoding at present in iris-grib, set to missing
    gribapi.grib_set(grib, "numberOfForecastsInEnsemble", 255)
    gribapi.grib_set(grib, "typeOfEnsembleForecast", 255)


def product_definition_template_common(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message that are common across
    all of the supported product definition templates.

    """
    set_discipline_and_parameter(cube, grib)

    # Various missing values.
    gribapi.grib_set(grib, "typeOfGeneratingProcess", 255)
    gribapi.grib_set(grib, "backgroundProcess", 255)
    gribapi.grib_set(grib, "generatingProcessIdentifier", 255)

    # Generic time handling.
    set_forecast_time(cube, grib)

    # Handle vertical coords.
    set_fixed_surfaces(cube, grib, full3d_cube)


def product_definition_template_0(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message based on Product
    Definition Template 4.0.

    Template 4.0 is used to represent an analysis or forecast at
    a horizontal level at a point in time.

    """
    gribapi.grib_set_long(grib, "productDefinitionTemplateNumber", 0)
    product_definition_template_common(cube, grib, full3d_cube)


def product_definition_template_1(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message based on Product
    Definition Template 4.1.

    Template 4.1 is used to represent an individual ensemble forecast, control
    and perturbed, at a horizontal level or in a horizontal layer at a point
    in time.

    """
    gribapi.grib_set(grib, "productDefinitionTemplateNumber", 1)
    product_definition_template_common(cube, grib, full3d_cube)
    set_ensemble(cube, grib)


def product_definition_template_8(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message based on Product
    Definition Template 4.8.

    Template 4.8 is used to represent an aggregation over a time
    interval.

    """
    gribapi.grib_set(grib, "productDefinitionTemplateNumber", 8)
    _product_definition_template_8_10_and_11(cube, grib)


def product_definition_template_10(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message based on Product Definition
    Template 4.10.

    Template 4.10 is used to represent a percentile forecast over a time
    interval.

    """
    gribapi.grib_set(grib, "productDefinitionTemplateNumber", 10)
    if not (cube.coords('percentile_over_time') and
            len(cube.coord('percentile_over_time').points) == 1):
        raise ValueError("A cube 'percentile_over_time' coordinate with one "
                         "point is required, but not present.")
    gribapi.grib_set(grib, "percentileValue",
                     int(cube.coord('percentile_over_time').points[0]))
    _product_definition_template_8_10_and_11(cube, grib)


def product_definition_template_11(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message based on Product
    Definition Template 4.11.

    Template 4.11 is used to represent an aggregation over a time
    interval for an ensemble member.

    """
    gribapi.grib_set(grib, "productDefinitionTemplateNumber", 11)
    set_ensemble(cube, grib)
    _product_definition_template_8_10_and_11(cube, grib)


def _product_definition_template_8_10_and_11(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message based on common aspects of
    Product Definition Templates 4.8 and 4.11.

    Templates 4.8 and 4.11 are used to represent aggregations over a time
    interval.

    """
    product_definition_template_common(cube, grib, full3d_cube)

    # Check for time coordinate.
    time_coord = cube.coord('time')

    if len(time_coord.points) != 1:
        msg = 'Expected length one time coordinate, got {} points'
        raise ValueError(msg.format(time_coord.points))

    if time_coord.nbounds != 2:
        msg = 'Expected time coordinate with two bounds, got {} bounds'
        raise ValueError(msg.format(time_coord.nbounds))

    # Extract the datetime-like object corresponding to the end of
    # the overall processing interval.
    end = time_coord.units.num2date(time_coord.bounds[0, -1])

    # Set the associated keys for the end of the interval (octets 35-41
    # in section 4).
    gribapi.grib_set(grib, "yearOfEndOfOverallTimeInterval", end.year)
    gribapi.grib_set(grib, "monthOfEndOfOverallTimeInterval", end.month)
    gribapi.grib_set(grib, "dayOfEndOfOverallTimeInterval", end.day)
    gribapi.grib_set(grib, "hourOfEndOfOverallTimeInterval", end.hour)
    gribapi.grib_set(grib, "minuteOfEndOfOverallTimeInterval", end.minute)
    gribapi.grib_set(grib, "secondOfEndOfOverallTimeInterval", end.second)

    # Only one time range specification. If there were a series of aggregations
    # (e.g. the mean of an accumulation) one might set this to a higher value,
    # but we currently only handle a single time related cell method.
    gribapi.grib_set(grib, "numberOfTimeRange", 1)
    gribapi.grib_set(grib, "numberOfMissingInStatisticalProcess", 0)

    # Period over which statistical processing is performed.
    set_time_range(time_coord, grib)

    # Check that there is one and only one cell method related to the
    # time coord.
    if cube.cell_methods:
        time_cell_methods = [
            cell_method for cell_method in cube.cell_methods if 'time' in
            cell_method.coord_names]
        if not time_cell_methods:
            raise ValueError("Expected a cell method with a coordinate name "
                             "of 'time'")
        if len(time_cell_methods) > 1:
            raise ValueError("Cannot handle multiple 'time' cell methods")
        cell_method, = time_cell_methods

        if len(cell_method.coord_names) > 1:
            raise ValueError("Cannot handle multiple coordinate names in "
                             "the time related cell method. Expected "
                             "('time',), got {!r}".format(
                                 cell_method.coord_names))

        # Type of statistical process (see code table 4.10)
        statistic_type = _STATISTIC_TYPE_NAMES.get(cell_method.method, 255)
        gribapi.grib_set(grib, "typeOfStatisticalProcessing", statistic_type)

        # Time increment i.e. interval of cell method (if any)
        set_time_increment(cell_method, grib)


def product_definition_template_15(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message based on Product
    Definition Template 4.15.

    Template 4.15 represents the type of spatial processing used to
    arrive at the given data value from the source data.

    """
    # Encode type of spatial processing (see code table 4.15)
    spatial_processing_type = cube.attributes['spatial_processing_type']
    spatial_processing = get_spatial_process_code(spatial_processing_type)

    # Encode statistical process and number of points
    # (see template definition 4.15)
    statistical_process = _SPATIAL_PROCESSING_TYPES[spatial_processing][1]
    number_of_points = _SPATIAL_PROCESSING_TYPES[spatial_processing][2]

    # Only a limited number of spatial processing types are supported.
    if spatial_processing not in _SPATIAL_PROCESSING_TYPES.keys():
        msg = ('Cannot save Product Definition Type 4.15 with spatial '
               'processing type {}'.format(spatial_processing))
        raise ValueError(msg)

    if statistical_process is not None:
        # Check the cube for statistical cell methods over area
        spatial_stats = _spatial_statistic(cube)
        # Identify the statistical method (e.g. 'mean') and encode it.
        if len(spatial_stats) > 0:
            cell_method_name = spatial_stats[0].method
            statistical_process = statistical_method_code(cell_method_name)
        else:
            raise ValueError("Could not find a suitable cell_method to save "
                             "as a spatial statistical process.")

    # Set GRIB messages
    gribapi.grib_set(grib, "productDefinitionTemplateNumber", 15)
    product_definition_template_common(cube, grib, full3d_cube)
    gribapi.grib_set(grib, "spatialProcessing", spatial_processing)
    if number_of_points is not None:
        gribapi.grib_set(grib, "numberOfPointsUsed", number_of_points)
    if statistical_process is not None:
        gribapi.grib_set(grib, "statisticalProcess", statistical_process)


def product_definition_template_40(cube, grib, full3d_cube=None):
    """
    Set keys within the provided grib message based on Product
    Definition Template 4.40.

    Template 4.40 is used to represent an analysis or forecast at a horizontal
    level or in a horizontal layer at a point in time for atmospheric chemical
    constituents.

    """
    gribapi.grib_set(grib, "productDefinitionTemplateNumber", 40)
    product_definition_template_common(cube, grib)
    constituent_type = cube.attributes['WMO_constituent_type']
    gribapi.grib_set(grib, "constituentType", constituent_type)


def product_definition_section(cube, grib, full3d_cube=None):
    """
    Set keys within the product definition section of the provided
    grib message based on the properties of the cube.

    """
    if not cube.coord("time").has_bounds():
        if cube.coords('realization'):
            # ensemble forecast (template 4.1)
            pdt = product_definition_template_1(cube, grib, full3d_cube)
        elif 'WMO_constituent_type' in cube.attributes:
            # forecast for atmospheric chemical constiuent (template 4.40)
            product_definition_template_40(cube, grib, full3d_cube)
        elif 'spatial_processing_type' in cube.attributes:
            # spatial process (template 4.15)
            product_definition_template_15(cube, grib, full3d_cube)
        else:
            # forecast (template 4.0)
            product_definition_template_0(cube, grib, full3d_cube)
    elif _cube_is_time_statistic(cube):
        if cube.coords('realization'):
            # time processed (template 4.11)
            pdt = product_definition_template_11
        elif cube.coords('percentile_over_time'):
            # time processed as percentile (template 4.10)
            pdt = product_definition_template_10
        else:
            # time processed (template 4.8)
            pdt = product_definition_template_8
        try:
            pdt(cube, grib, full3d_cube)
        except ValueError as e:
            raise ValueError('Saving to GRIB2 failed: the cube is not suitable'
                             ' for saving as a time processed statistic GRIB'
                             ' message. {}'.format(e))
    else:
        # Don't know how to handle this kind of data
        msg = 'A suitable product template could not be deduced'
        raise TranslationError(msg)


###############################################################################
#
# Data Representation Section 5
#
###############################################################################

def data_section(cube, grib):
    # Masked data?
    if ma.isMaskedArray(cube.data):
        if not np.isnan(cube.data.fill_value):
            # Use the data's fill value.
            fill_value = float(cube.data.fill_value)
        else:
            # We can't use the cube's fill value if it's NaN,
            # the GRIB API doesn't like it.
            # Calculate an MDI outside the data range.
            min, max = cube.data.min(), cube.data.max()
            fill_value = min - (max - min) * 0.1
        # Prepare the unmasked data array, using fill_value as the MDI.
        data = cube.data.filled(fill_value)
    else:
        fill_value = None
        data = cube.data

    # units scaling
    grib2_info = gptx.cf_phenom_to_grib2_info(cube.standard_name,
                                              cube.long_name)
    if grib2_info is None:
        # for now, just allow this
        warnings.warn('Unable to determine Grib2 parameter code for cube.\n'
                      'Message data may not be correctly scaled.')
    else:
        if cube.units != grib2_info.units:
            data = cube.units.convert(data, grib2_info.units)
            if fill_value is not None:
                fill_value = cube.units.convert(fill_value, grib2_info.units)

    if fill_value is None:
        # Disable missing values in the grib message.
        gribapi.grib_set(grib, "bitmapPresent", 0)
    else:
        # Enable missing values in the grib message.
        gribapi.grib_set(grib, "bitmapPresent", 1)
        gribapi.grib_set_double(grib, "missingValue", fill_value)

    gribapi.grib_set_double_array(grib, "values", data.flatten())

    # todo: check packing accuracy?
#    print("packingError", gribapi.getb_get_double(grib, "packingError"))


###############################################################################

def gribbability_check(cube):
    "We always need the following things for grib saving."

    # GeogCS exists?
    cs0 = cube.coord(dimensions=[0]).coord_system
    cs1 = cube.coord(dimensions=[1]).coord_system
    if cs0 is None or cs1 is None:
        raise TranslationError("CoordSystem not present")
    if cs0 != cs1:
        raise TranslationError("Inconsistent CoordSystems")

    # Time period exists?
    if not cube.coords("time"):
        raise TranslationError("time coord not found")


def run(slice2d_cube, grib, full3d_cube):
    """
    Set the keys of the grib message based on the contents of the slice2d_cube.

    Args:

    * slice2d_cube:
        A :class:`iris.slice2d_cube.Cube` representing a 2d field.

    * grib_message_id:
        ID of a grib message in memory. This is typically the return value of
        :func:`gribapi.grib_new_from_samples`.

    * full3d_cube:
        A :class:`iris.slice2d_cube.Cube` representing the entire save cube.
        This is required to write data with hybrid vertical coordinates, as
        the GRIB2 spec records hybrid coefficients for *all* the levels in
        every message.

    """
    gribbability_check(slice2d_cube)

    # Section 1 - Identification Section.
    identification(slice2d_cube, grib)

    # Section 3 - Grid Definition Section (Grid Definition Template)
    grid_definition_section(slice2d_cube, grib)

    # Section 4 - Product Definition Section (Product Definition Template)
    product_definition_section(slice2d_cube, grib, full3d_cube)

    # Section 5 - Data Representation Section (Data Representation Template)
    data_section(slice2d_cube, grib)
