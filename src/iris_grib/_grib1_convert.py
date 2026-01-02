# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Module to support loading of GRIB1 data.

Converts a GRIB1 message into cube metadata.

This is a re-implementation of '._grib1_legacy.grib1_load_rules', but now using a
:class:`iris_grib.message.GribMessage` in place of a
:class:`iris_grib._grib1_legacy.grib_wrapper.GribWrapper`.
"""

import dataclasses
import datetime
from typing import Any, Tuple
import warnings

from cf_units import Unit
import eccodes

import numpy as np
from iris.coord_systems import CoordSystem

from iris.coords import AuxCoord, DimCoord
from iris import coord_systems
from iris.exceptions import TranslationError
from iris.fileformats.rules import (
    ConversionMetadata,
)

from iris_grib._load_convert import options
from iris_grib.message import GribMessage, Section
from iris_grib import grib_phenom_translation as gptx

# _CENTRE_NAME_NUMBERS_BACKREFS = {
#     "egrr": 74,
#     "ecmwf": 98,
# }


def _problem_msg(
        base_msg: str, n_section: int, key: str | None = None, value: Any = None
    ):
    msg = f"{base_msg} : section {n_section}"
    if key is not None:
        msg += f", '{key!s}'={value!r}."
    return msg


def translation_error(
        base_msg: str, n_section: int, key: str | None = None, value: Any = None
    ):
    msg = "GRIB1 translation error, unsupported metadata. " + base_msg
    msg = _problem_msg(msg, n_section, key, value)
    return TranslationError(msg)


def warn_unsupported(
        base_msg: str, n_section: int, key: str | None = None, value: Any =None
    ):
    if options.warn_on_unsupported:
        msg = _problem_msg(base_msg, n_section, key, value)
        warnings.warn(msg)


def convert_phenomenon(field: GribMessage, metadata: ConversionMetadata):
    section1 = field.sections[1]

    tables_version = section1["table2Version"]
    centre_name = section1["centre"]
    # It seems that, for GRIB1, we have no access to the original number here.
    # centre_number = _CENTRE_NAME_NUMBERS_BACKREFS.get(centre_name, 0)

    # Reading "centre" from the section gives a short-code string interpretation, since
    #  this is the "native type" given by eccodes.
    # To get the actual number code recorded in the file, we must bypass the GribMessage
    # sections structure + use eccodes directly (Yuck!).
    centre_number = eccodes.codes_get_long(field._raw_message._message_id, "centre")
    param_number = section1["indicatorOfParameter"]
    grib_code = gptx.GRIBCode(
        edition=1,
        table_version=tables_version,
        centre_number=centre_number,
        number=param_number,
    )
    metadata["attributes"]["GRIB_PARAM"] = grib_code

    cf_data = gptx.grib1_phenom_to_cf_info(
        table2_version=tables_version,
        centre_number=centre_number,
        param_number=param_number,
    )
    standard_name, long_name, units = None, None, None
    if cf_data is not None:
        standard_name = cf_data.standard_name
        long_name = cf_data.standard_name or cf_data.long_name
        units = cf_data.units
    elif tables_version < 128:
        # built-in decodes...
        match param_number:
            case 11:
                standard_name = "air_temperature"
                units = "kelvin"

            case 33:
                standard_name = "x_wind"
                units = "m s-1"

            case 34:
                standard_name = "y_wind"
                units = "m s-1"

    if tables_version >= 128 or (tables_version == 1 and param_number >= 128):
        long_name = f"UNKNOWN LOCAL PARAM {param_number}.{tables_version}"
        units = "???"

    metadata["standard_name"] = standard_name
    metadata["long_name"] = long_name
    metadata["units"] = units


_SUPPORTED_GRID_TYPES = {
    0: "latlon",
    3: "lambert_conformal",
    4: "gaussian",
    5: "polar_stereo",
    10: "rotated_latlon",
}

@dataclasses.dataclass
class XyDetail:
    x0: float | None = None
    y0: float | None = None
    x1: float | None = None
    y1: float | None = None
    nx: int | None = None
    ny: int | None = None
    dx: float | None = None
    dy: float | None = None
    nxy_names: Tuple[str, str] | None = None
    dxy_names: Tuple[str, str] | None = None

    @classmethod
    def from_field(cls, field: GribMessage):
        section2 = field.sections[2]
        # these names are used for any grids, but not present for all
        x0 = section2.get("longitudeOfFirstGridPoint", None)
        x1 = section2.get("longitudeOfLastGridPoint", None)
        y0 = section2.get("latitudeOfFirstGridPoint", None)
        y1 = section2.get("latitudeOfLastGridPoint", None)
        # Coordinate key names vary by grid type, and in most cases can also be missing
        grid_code = section2["dataRepresentationType"]
        grid_name = _SUPPORTED_GRID_TYPES[grid_code]
        if grid_name in ("latlon", "rotated_latlon", "gaussian"):
            dxy_names = "iDirectionIncrement", "jDirectionIncrement"
            nxy_names = "Ni", "Nj"
        else:
            dxy_names = "DxInMetres", "DyInMetres"
            nxy_names = "Nx", "Ny"

        nx, ny = [section2.get(nxy_name, None) for nxy_name in nxy_names]
        dx, dy = [section2.get(dxy_name, None) for dxy_name in dxy_names]
        result = cls(
            x0=x0, y0=y0, x1=x1, y1=y1,
            nx=nx, ny=ny, dx=dx, dy=dy,
            nxy_names=nxy_names, dxy_names=dxy_names,
        )
        return result


def _decode_xy_values(field: GribMessage) -> (np.ndarray, np.ndarray, bool):
    section2 = field.sections[2]
    grid_code = section2["dataRepresentationType"]
    grid_name = _SUPPORTED_GRID_TYPES[grid_code]

    xy_detail = XyDetail.from_field(field)
    x0, x1, y0, y1 = xy_detail.x0, xy_detail.x1, xy_detail.y0, xy_detail.y1
    nx, ny, dx, dy = xy_detail.nx, xy_detail.ny, xy_detail.dx, xy_detail.dy
    nxy_names = xy_detail.nxy_names
    dxy_names = xy_detail.dxy_names

    scanning_mode = section2["scanningMode"]
    # Extract the only bit which we understand (for now)
    y_negative = (scanning_mode & 64) != 0
    if (scanning_mode & ~64) != 0:
        raise translation_error(
            "unsupported grid scanning mode",
            2, "scanningMode", scanning_mode
        )

    # Now get the X and Y points arrays.
    # Note that we need to support 'reduced' grids, which are not totally irregular, but
    #  in which the number of points in a row *changes* with latitude.
    #  We can only represent these as 1-D mesh-like (or trajectory-like) cubes.

    def check_redundant_v0_v1_nv_dv(dxy_name, xy0, xy1, nxy):
        dxy = section2.get(dxy_name, None)
        dx_calc = (xy1 - xy0) / (nxy - 1)
        if not np.allclose(dx_calc, dxy, atol=1e-5):
            msg = (
                f"bad {dxy_name!r} doesn't match "
                f"(xy?1 - xy?0) / (n?xy - 1) * 1000 ={dx_calc}."
            )
            # TODO: make this an error
            # raise translation_error(msg, 2, dxy_name, dxy)
            warn_unsupported(msg, 2, dxy_name, dxy)


    mdeg = 0.001
    if nx is None:
        raise translation_error(
            "irregular x points not supported",
            2, nxy_names[0], None
        )
    else:
        x_values = np.linspace(x0 * mdeg, x1 * mdeg, nx, endpoint=True)
        check_redundant_v0_v1_nv_dv(dxy_names[0], x0, x1, nx)

    if ny is not None:
        # regular separate X+Y coords
        is_regular = True
        y_values = np.linspace(y0 * mdeg, y1 * mdeg, ny, endpoint=True)
        check_redundant_v0_v1_nv_dv(dxy_names[1], y0, y1, ny)

    else:
        # missing n-columns --> irregular numbers of points per row
        is_regular = False
        if grid_name not in ("gaussian", "latlon"):
            raise translation_error(
                (
                    f"unsupported grid type ('dataRepresentationType'={grid_code}) "
                    "for irregular y values"
                ),
                2, "Nj", None
            )
        if grid_name == "gaussian":
            # this is rather horrible
            # NOTE: gaussian grids -- the required calculation is really complex
            #  see: https://github.com/ecmwf/eccodes/blob/2.44.2/src/eccodes/geo/grib_geography.cc#L97
            # I'm giving up here + using the implementation built into eccodes
            x_values = eccodes.codes_get_double_array(
                field._raw_message._message_id,
                "longitudes"
            )
            y_values = eccodes.codes_get_double_array(
                field._raw_message._message_id,
                "latitudes"
            )
        else:
            # Not *quite* so nasty : the x values in each row are regular, and we can
            #  calculate the correct values.
            row_lengths = section2["pl"]
            x_values = np.array([], dtype=np.float64)
            for nx in row_lengths.astype(int):
                xs = np.linspace(x0, x1, nx, endpoint=True)
                x_values = np.concatenate([x_values, xs])
            # NOTE: there is no scaling in this case
            y_values = np.linspace(y0, y1, ny, endpoint=True)

    return x_values, y_values, is_regular


def _ellipsoid(section2: Section) -> CoordSystem:
    grid_name = _SUPPORTED_GRID_TYPES[section2["dataRepresentationType"]]
    # shape of the Earth
    resolutionAndComponentFlags = section2["resolutionAndComponentFlags"]
    oblate_Earth = resolutionAndComponentFlags & 0b0100000
    if oblate_Earth:
        # Earth assumed oblate spheroidal with size as determined by IAU in
        # 1965 (6378.160 km, 6356.775 km, f = 1/297.0)
        msg = (
            "Oblate Spheroidal Earth not supported: "
            f"resolutionAndComponentFlags=0b{resolutionAndComponentFlags:08b}."
        )
        raise translation_error(
            "Oblate Spheroidal Earth not supported",
            2, "resolutionAndComponentFlags", resolutionAndComponentFlags
        )
    else:
        # Earth assumed spherical with radius 6367.47 km
        ellipsoid = coord_systems.GeogCS(semi_major_axis=6367470)
    return ellipsoid


def _coord_system(section2: Section) -> CoordSystem:
    grid_name = _SUPPORTED_GRID_TYPES[section2["dataRepresentationType"]]

    # shape of the Earth
    ellipsoid = _ellipsoid(section2)

    if grid_name in ("polar_stereo", "lambert_conformal"):
        pcf = section2["projectionCentreFlag"]
        grid_orientation_degrees = section2["LoV"]
        truescale_lat = 60.0  # this is FIXED for grib1
        match pcf:
            case 0:
                pole_lat = 90.
            case 128:
                pole_lat = -90.
            case _:
                raise translation_error(
                    "unexpected projection centre flags",
                    2, "projectionCentreFlag", pcf
                )

    if grid_name in ("gaussian", "latlon"):
        coord_system = ellipsoid
    elif grid_name == "rotated_latlon":
        spole_lon = 0.001 * section2["longitudeOfSouthernPole"]
        spole_lat = 0.001 * section2["latitudeOfSouthernPole"]
        rot_ang = section2["angleOfRotationInDegrees"]
        geoid = coord_systems.GeogCS(semi_major_axis=6367470)
        coord_system = coord_systems.RotatedGeogCS(
            -spole_lat,
            (spole_lon + 180.0) % 360.0,
            ellipsoid=ellipsoid,
        )
    elif grid_name == "polar_stereo":
        coord_system = coord_systems.PolarStereographic(
            pole_lat_lat=0,
            central_lon=grid_orientation_degrees,
            true_scale_lat=truescale_lat,  # this is a CONSTANT for grib1
            ellipsoid=ellipsoid
        )
    elif grid_name == "lambert_conformal":
        secant_lats = (section2["Latin1"] * 0.001, section2["Latin1"] * 0.001)
        coord_system = coord_systems.LambertConformal(
            central_lat=truescale_lat,  # this is a CONSTANT for grib1
            central_lon=grid_orientation_degrees,
            secant_latitudes=secant_lats,
            ellipsoid=ellipsoid,
        )

    return coord_system


# _SUPPORTED_GRID_TYPES = {
#     0: "latlon",
#     3: "lambert_conformal",
#     4: "gaussian",
#     5: "polar_stereo",
#     10: "rotated_latlon",
# }
def convert_horizontal(field: GribMessage, metadata: ConversionMetadata):
    section2 = field.sections[2]
    grid_type = section2["dataRepresentationType"]
    if grid_type not in _SUPPORTED_GRID_TYPES:
        raise translation_error(
            "unrecognised/unsupported grid type",
            2, "dataRepresentationType", grid_type
        )

    grid_name = _SUPPORTED_GRID_TYPES[section2["dataRepresentationType"]]
    if grid_name in ("gaussian", "latlon"):
        xname, yname = "longitude", "latitude"
        xyunits = "degrees"
    elif grid_name == "rotated_latlon":
        xname, yname = "grid_longitude", "grid_latitude"
        xyunits = "degrees"
    elif grid_name == "polar_stereo":
        xname, yname = "projection_x_coordinate", "projection_y_coordinate"
        xyunits = "m"
    elif grid_name == "lambert_conformal":
        xname, yname = "projection_x_coordinate", "projection_y_coordinate"
        xyunits = "m"

    coord_system = _coord_system(section2)
    xvals, yvals, is_regular = _decode_xy_values(field)

    if is_regular:
        coord_class = DimCoord
        coords = metadata["dim_coords_and_dims"]
    else:
        coord_class = AuxCoord
        coords = metadata["aux_coords_and_dims"]
    x_coord, y_coord = [
        coord_class(
            covals,
            coname,
            units=xyunits,
            coord_system=coord_system,
        )
        for coname, covals in zip([xname, yname], [xvals, yvals])
    ]
    coords.extend([
        (y_coord, 0,),
        (x_coord, 1 if is_regular else 0)
    ])


_SUPPORTED_TIMERANGE_TYPES = {
    # values are names for creating a period cell method
    0: None,
    # 2: None,
    3: "mean",
    4: "sum",
    10: None,  # extended-range reference time
    # 5: "_difference",
    # 118: "_covariance",
    # 125: "standard_deviation",
}
# N.B. there are ***multiple*** duplicates.
# Don't distinguish (for now).
# TODO: are these all actually valid ?
for n_code in (51, 113, 117, 123):
    _SUPPORTED_TIMERANGE_TYPES[n_code] = "mean"
for n_code in (114, 124):
    _SUPPORTED_TIMERANGE_TYPES[n_code] = "sum"

_SUPPORTED_TIME_UNITS = {
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
    254: ("seconds", 1)
}


def convert_time(field: GribMessage, metadata: ConversionMetadata):
    section1 = field.sections[1]
    aux_coords = metadata["aux_coords_and_dims"]
    basetime_unit = Unit("hours since epoch", "gregorian")

    time_parts = [
        section1[key]
        for key in ["yearOfCentury", "month", "day", "hour", "minute"]
    ]
    century = section1["centuryOfReferenceTimeOfData"]

    # This never fails ?
    assert all(part is not None for part in time_parts + [century])

    # There is at least enough valid information to create time coordinate(s)
    time_parts[0] += 100 * century
    ref_timedate = datetime.datetime(*time_parts)
    reftime_units = Unit("hours since epoch", "gregorian")

    timerange_code = section1["timeRangeIndicator"]
    if timerange_code not in _SUPPORTED_TIMERANGE_TYPES:
        raise translation_error("unsupported timerange type.", 1, "indicatorOfUnitOfTimeRange", timerange_code)

    timerange_name, timerange_seconds = _SUPPORTED_TIME_UNITS[timerange_code]
    p1, p2 = [section1[name] for name in ("P1", "P2")]

    period_statistic = _SUPPORTED_TIMERANGE_TYPES[timerange_code]
    if period_statistic is None:
        aux_coords.extend([
            (
                DimCoord(
                    points=[p1],
                    standard_name="forecast_period",
                    units=timerange_name,
                ),
                0
            ),
            (
                DimCoord(
                    points=p1,
                    standard_name="time",
                    units=f"hours since epoch",
                ),
                0
            ),
        ])
    else:
        aux_coords.extend([
            (
                DimCoord(
                    points=[p1],
                    standard_name="forecast_period",
                    units=timerange_name,
                ),
                0
            ),
            (
                DimCoord(
                    points=[p1],
                    standard_name="time",
                    units=f"{timerange_name} since epoch",
                ),
                0
            ),
        ])


def validate(field: GribMessage):
    # Raise problems with construction which the translation code can't accept.
    if not 2 in field.sections:
        raise translation_error(f"message with no section 2 (grid)")

    user_grid = field.sections[1]["gridDefinition"]
    if user_grid != 255:
        warn_unsupported("originator-defined grid code", 1, "gridDefinition", user_grid)

    process_id = field.sections[1]["generatingProcessIdentifier"]
    if process_id != 255:
        warn_unsupported(
            "originator-defined process code", 1,
            "generatingProcessIdentifier", process_id
        )



def grib1_convert(field: GribMessage, metadata: ConversionMetadata):
    assert hasattr(field, "sections")
    assert field.sections[0]["editionNumber"] == 1

    # Checks for odd metadata cases that we can't handle
    validate(field)

    # product definitions :  mostly section 1
    convert_phenomenon(field, metadata)

    # time coords and cell-methods :  mostly section 1
    convert_time(field, metadata)

    # vertical layer definition :  mostly section 2
    # convert_vertical(field, metadata)

    # horizontal grid :  mostly section 2
    # N.B. this one **has** to take "field", so we can still use computed keys (yuck!)
    convert_horizontal(field, metadata)
