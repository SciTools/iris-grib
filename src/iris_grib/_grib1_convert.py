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
from typing import Any
import warnings

from cf_units import Unit
import eccodes

import numpy as np
from iris.coord_systems import CoordSystem

from iris.aux_factory import HybridPressureFactory
from iris.coords import AuxCoord, CellMethod, DimCoord
from iris import coord_systems
from iris.exceptions import TranslationError
from iris.fileformats.rules import ConversionMetadata, Factory, Reference

from iris_grib._load_convert import options
from iris_grib.message import GribMessage, Section
from iris_grib import grib_phenom_translation as gptx


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
    base_msg: str, n_section: int, key: str | None = None, value: Any = None
):
    if options.warn_on_unsupported:
        msg = _problem_msg(base_msg, n_section, key, value)
        warnings.warn(msg)


def convert_phenomenon(field: GribMessage, metadata: ConversionMetadata):
    section1 = field.sections[1]

    tables_version = section1["table2Version"]
    # centre_name = section1["centre"]
    # # It seems that, for GRIB1, we have no access to the original number here.
    # # centre_number = _CENTRE_NAME_NUMBERS_BACKREFS.get(centre_name, 0)

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

    # For some odd reason the old code creates an auxcoord from the centre code,
    #  so replicate that for backwards compatibility
    if centre_number != 0:
        centre_title = KNOWN_CENTRE_TITLES.get(
            centre_number, f"unknown centre {centre_number!s}"
        )
        metadata["aux_coords_and_dims"].append(
            (
                AuxCoord(
                    points=centre_title,
                    long_name="originating_centre",
                    units="no_unit",
                ),
                None,
            )
        )

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

    if (tables_version >= 128 and cf_data is None) or (
        tables_version == 1 and param_number >= 128
    ):
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
    nxy_names: tuple[str, str] | None = None
    dxy_names: tuple[str, str] | None = None

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
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            nx=nx,
            ny=ny,
            dx=dx,
            dy=dy,
            nxy_names=nxy_names,
            dxy_names=dxy_names,
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
            "unsupported grid scanning mode", 2, "scanningMode", scanning_mode
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
            "irregular x points not supported", 2, nxy_names[0], None
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
                2,
                "Nj",
                None,
            )
        if grid_name == "gaussian":
            # this is rather horrible
            # NOTE: gaussian grids -- the required calculation is really complex
            #  see: https://github.com/ecmwf/eccodes/blob/2.44.2/src/eccodes/geo/grib_geography.cc#L97
            # I'm giving up here + using the implementation built into eccodes
            x_values = eccodes.codes_get_double_array(
                field._raw_message._message_id, "longitudes"
            )
            y_values = eccodes.codes_get_double_array(
                field._raw_message._message_id, "latitudes"
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
            2,
            "resolutionAndComponentFlags",
            resolutionAndComponentFlags,
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
        if grid_name == "polar_stereo":
            orientation_keyname = "orientationOfTheGrid"
        else:
            # different for lambert (!yuck!)
            orientation_keyname = "LoV"
        grid_orientation_degrees = section2[orientation_keyname]
        truescale_lat = 60.0  # this is FIXED for grib1
        match pcf:
            case 0:
                pole_lat = 90.0
            case 128:
                pole_lat = -90.0
            case _:
                raise translation_error(
                    "unexpected projection centre flags", 2, "projectionCentreFlag", pcf
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
            central_lat=pole_lat,
            central_lon=grid_orientation_degrees,
            true_scale_lat=truescale_lat,  # this is a CONSTANT for grib1
            ellipsoid=ellipsoid,
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
            "unrecognised/unsupported grid type", 2, "dataRepresentationType", grid_type
        )

    grid_name = _SUPPORTED_GRID_TYPES[section2["dataRepresentationType"]]
    if grid_name in ("gaussian", "latlon"):
        xname, yname = "longitude", "latitude"
        xyunits = "degrees"
    elif grid_name == "rotated_latlon":
        xname, yname = "grid_longitude", "grid_latitude"
        xyunits = "degrees"
    elif grid_name == "polar_stereo" or grid_name == "lambert_conformal":
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

    def _is_circular_lons(points, name):
        # Work out whether to set "circular" on the coord we are about to make.
        # N.B. explicitly restricted to *longitude* coords
        cyclic = False
        if "longitude" in name.lower() and points.shape[0] > 1:
            max_step = np.abs(np.diff(points)).max()
            wrapping_gap = 360.0 - abs(points[-1] - points[0])
            if wrapping_gap <= max_step:
                # Always consider circular if the gap is actually *smaller* than the step
                cyclic = True
            else:
                # If the gap is bigger, allow a 0.1% tolerance
                cyclic = abs(wrapping_gap / max_step - 1) < 0.001
        return cyclic

    x_coord, y_coord = [
        coord_class(
            covals,
            coname,
            units=xyunits,
            coord_system=coord_system,
            circular=_is_circular_lons(covals, coname),
        )
        for coname, covals in zip([xname, yname], [xvals, yvals])
    ]
    coords.extend(
        [
            (
                y_coord,
                0,
            ),
            (x_coord, 1 if is_regular else 0),
        ]
    )


# partial decoding of 'timeRangeIndicator' ==> code table 5
# N.B. there are ***multiple*** duplicates.
# We don't distinguish these (for now).
# TODO: are these all actually valid ?
_SUPPORTED_TIMERANGE_TYPES = {
    # values are ("name for period cell method", "is_bounded")
    0: (None, False),  # single timepoint
    1: (
        None,
        False,
    ),  # single timepoint, "initialised analysis" instead (?) of forecast
    2: (None, True),  # bounded timepoint -- no statistic
    3: ("mean", True),
    4: ("sum", True),
    5: ("_difference", True),
    10: (None, False),  # as 0, but with extended-range reference time
    113: ("mean", True),
    118: ("_covariance", True),
    123: ("mean", True),
    124: ("sum", True),
}

# partial decoding of 'timeRangeIndicator' ==> code table 4
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
    254: ("seconds", 1),
}

KNOWN_CENTRE_TITLES = {
    7: "US National Weather Service, National Centres for Environmental Prediction",
    34: "Tokyo, Japan Meteorological Agency",
    55: "San Francisco",
    74: "U.K. Met Office - Exeter",
    98: "European Centre for Medium Range Weather Forecasts",
}


def convert_time(field: GribMessage, metadata: ConversionMetadata):
    section1 = field.sections[1]
    aux_coords = metadata["aux_coords_and_dims"]
    basetime_unit = Unit("hours since epoch", "gregorian")

    time_parts = [
        section1[key] for key in ["yearOfCentury", "month", "day", "hour", "minute"]
    ]
    century = section1["centuryOfReferenceTimeOfData"]

    # This never fails ?
    assert all(part is not None for part in time_parts + [century])

    # There is at least enough valid information to create time coordinate(s)
    time_parts[0] += 100 * (century - 1)
    reftime_dt = datetime.datetime(*time_parts)

    # N.B. our times are always output with a standard epoch-relative unit.
    # Not so obvious, as messages do mostly have ref time + forecast_period, but this
    #  form is required for backwards compatibility.
    time_output_units = Unit("hours since epoch", calendar="gregorian")

    timerange_code = section1["timeRangeIndicator"]
    if timerange_code not in _SUPPORTED_TIMERANGE_TYPES:
        raise translation_error(
            "unsupported timerange type.", 1, "timeRangeIndicator", timerange_code
        )

    timeunits_code = section1["unitOfTimeRange"]
    timeunits_name, timeunits_seconds = _SUPPORTED_TIME_UNITS[timeunits_code]
    timeunit_delta = datetime.timedelta(seconds=timeunits_seconds)

    epoch_datetime = time_output_units.num2date(0.0)

    def convert_timepoint_from_reftime_to_epoch(
        t_from_ref: float, epoch_units_delta=timeunit_delta
    ):
        timepoint_ref_delta = t_from_ref * timeunit_delta
        timepoint_datetime = reftime_dt + timepoint_ref_delta
        timepoint_epoch_delta = timepoint_datetime - epoch_datetime
        t_from_epoch = timepoint_epoch_delta.total_seconds() / timeunits_seconds
        return t_from_epoch

    p1, p2 = [section1[name] for name in ("P1", "P2")]

    period_stat_name, is_bounded = _SUPPORTED_TIMERANGE_TYPES[timerange_code]
    if not is_bounded:
        fp_dtype = np.int32
        fp_points = [p1]
        fp_bounds = None
        # For backward compatibility, the output time values must be given in
        #  "hours since epoch", not relative to the reference time
        #  (and we don't provide a reference_time coord, either).
        # So we add difference between ref time and epoch start to the time values.
        time_points = [convert_timepoint_from_reftime_to_epoch(p1)]
        time_bounds = None
    else:
        fp_dtype = np.float64
        fp_points = [0.5 * (p1 + p2)]
        fp_bounds = [p1, p2]
        p1_epoch, p2_epoch = [
            convert_timepoint_from_reftime_to_epoch(timeval) for timeval in (p1, p2)
        ]
        time_points = [0.5 * (p1_epoch + p2_epoch)]
        time_bounds = [p1_epoch, p2_epoch]

    aux_coords.extend(
        [
            (
                DimCoord(
                    points=np.array(fp_points, dtype=fp_dtype),
                    bounds=np.array(fp_bounds, dtype=fp_dtype) if fp_bounds else None,
                    standard_name="forecast_period",
                    units=timeunits_name,
                ),
                None,
            ),
            (
                DimCoord(
                    points=np.array(time_points),
                    bounds=np.array(time_bounds) if time_bounds else None,
                    standard_name="time",
                    units=time_output_units,
                ),
                None,
            ),
        ]
    )

    # For stats, also add a cell method
    if period_stat_name:
        metadata["cell_methods"].append(CellMethod(period_stat_name, coords="time"))


def validate(field: GribMessage):
    # Raise problems with construction which the translation code can't accept.
    if 2 not in field.sections:
        raise translation_error("message with no section 2 (grid)")

    user_grid = field.sections[1]["gridDefinition"]
    if user_grid != 255:
        warn_unsupported("originator-defined grid code", 1, "gridDefinition", user_grid)

    process_id = field.sections[1]["generatingProcessIdentifier"]
    if process_id != 255:
        warn_unsupported(
            "originator-defined process code",
            1,
            "generatingProcessIdentifier",
            process_id,
        )


def convert_vertical(field: GribMessage, metadata: ConversionMetadata):
    # vertical layer definition :  mostly section 2
    section1 = field.sections[1]
    aux_coords = metadata["aux_coords_and_dims"]
    # leveltype_code = section1["indicatorOfTypeOfLevel"]
    # Once again the "default fetch type" returns a coded string, and we'd rather have
    #  the original number code, but this requires looking inside the box..
    leveltype_code = eccodes.codes_get_long(
        field._raw_message._message_id, "indicatorOfTypeOfLevel"
    )
    if leveltype_code == 1:
        # Surface level : nothing to do
        pass
    elif leveltype_code == 100:
        # pressure level
        level_value = section1["level"]
        level_points = np.array([level_value], dtype=np.int32)
        aux_coords.append(
            (DimCoord(points=level_points, long_name="pressure", units="hPa"), None)
        )
    elif leveltype_code == 102:
        # bounded pressure levels
        level_values = [section1["bottomOfLevel"], section1["topOfLevel"]]
        level_bounds = np.array(level_values, dtype=np.int32)
        level_points = level_bounds.mean()
        aux_coords.append(
            (
                DimCoord(
                    points=level_points,
                    bounds=level_bounds,
                    standard_name="pressure",
                    units="hPa",
                ),
                None,
            )
        )
    elif leveltype_code == 105:
        # single height above ground
        level_value = section1["level"]
        level_points = np.array([level_value], dtype=np.int32)
        aux_coords.append(
            (DimCoord(points=level_points, long_name="height", units="m"), None)
        )
    elif leveltype_code == 109:
        # "hybrid levels" == ECMWF-style hybrid pressure
        level_value = section1["level"]
        pv = field.sections[2].get("pv")
        if pv is None:
            raise translation_error(
                base_msg="Missing 'pv' coefficients for hybrid levels.",
                n_section=1,
                key="pv",
                value=None,
            )
        aux_coords.extend(
            [
                (
                    AuxCoord(
                        level_value,
                        standard_name="model_level_number",
                        units=1,
                        attributes={"positive": "up"},
                    ),
                    None,
                ),
                (
                    DimCoord(pv[level_value], long_name="level_pressure", units="Pa"),
                    None,
                ),
                (
                    AuxCoord(
                        pv[len(pv) // 2 + level_value],
                        long_name="sigma",
                        units=1,
                    ),
                    None,
                ),
            ]
        )

        metadata["factories"].append(
            Factory(
                HybridPressureFactory,
                [
                    {"long_name": "level_pressure"},
                    {"long_name": "sigma"},
                    Reference("surface_pressure"),
                ],
            )
        )

    else:
        raise translation_error(
            base_msg="Unsupported/unknown vertical level type",
            n_section=1,
            key="indicatorOfTypeOfLevel",
            value=leveltype_code,
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

    # vertical layer definition :  mostly section 1, but hybrid levels in section 2
    convert_vertical(field, metadata)

    # horizontal grid :  mostly section 2
    # N.B. this one **has** to take "field", so we can still use computed keys (yuck!)
    convert_horizontal(field, metadata)
