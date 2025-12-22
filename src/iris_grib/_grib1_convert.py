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
from typing import Any
import warnings

import eccodes

import numpy as np
from iris.coord_systems import CoordSystem

from iris.coords import DimCoord
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


def translation_error(base_msg: str, n_section: int, key: str | None = None, value: Any =None):
    msg = _problem_msg(base_msg, n_section, key, value)
    return TranslationError("GRIB1 translation warning, unsupported metadata " + msg)


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
    # sections structure + use eccodes directly.
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


def _decode_xy_values(field: GribMessage) -> (np.ndarray, np.ndarray):
    section2 = field.sections[2]
    grid_code = section2["dataRepresentationType"]
    grid_name = _SUPPORTED_GRID_TYPES[grid_code]

    # these names are used for any grids, but not present for all
    x0 = section2.get("longitudeOfFirstGridPoint", None)
    x1 = section2.get("longitudeOfLastGridPoint", None)
    y0 = section2.get("latitudeOfFirstGridPoint", None)
    y1 = section2.get("latitudeOfLastGridPoint", None)
    # the increment names vary by grid type, and may also be absent in most cases
    if grid_name in ("latlon", "rotated_latlon", "gaussian"):
        dx = section2.get("iDirectionIncrement", None)
        dy = section2.get("jDirectionIncrement", None)
        nx = section2.get("Ni", None)
        ny = section2.get("Nj", None)
    else:
        dx = section2.get("DxInMetres", None)
        dy = section2.get("DyInMetres", None)
        nx = section2.get("Nx", None)
        ny = section2.get("Ny", None)

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
    #  have numbers of points in a row differing at different latitudes.
    #  We can only represent these as 1-D mesh-like (or trajectory-like) cubes.

    if nx is None:
        raise translation_error(
            "irregular x points not supported",
            2, "Ni", None
        )
    x0, x1 = 0., 180.

    if ny is not None:
        # regular separate X+Y coords
        pass
    else:
        # missing n-columns --> irregular numbers of points per row
        if grid_name not in ("gaussian", "latlon"):
            raise translation_error(
                (
                    f"unsupported grid type ('dataRepresentationType'={grid_code}) "
                    "for irregular y values"
                ),
                2, "Nj", None
            )
        if grid_name == "gaussian":
            # this is horrible
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
            # Not *quite* so nasty : the x values are regular (probably), and we can
            #  calculate the correct values.
            row_lengths = section2["pl"]
            y_values = np.array([], dtype=np.float64)
            for nx in row_lengths.astype(int):
                xs = np.linspace(x0, x1, nx, endpoint=True)
                y_values = np.concatenate([y_values, xs])



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
        raise TranslationError(msg)
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
    elif grid_name == "rotated_latlon":
        xname, yname = "grid_longitude", "grid_latitude"
    elif grid_name == "polar_stereo":
        xname, yname = "projection_x_coordinate", "projection_y_coordinate"
    elif grid_name == "lambert_conformal":
        xname, yname = "projection_x_coordinate", "projection_y_coordinate"

    coord_system = _coord_system(section2)
    xvals, yvals = _decode_xy_values(field)

    dim_coords_and_dims = metadata["dim_coords_and_dims"]
    if grid_name in ("latlon", "rotated_latlon"):
        # (rotated) latitude-longitude

        # just pin this aspect for now
        scanning_code = section2["scanningMode"]
        # scanning_code &= 7  # only 3 bits significant??
        # TODO: don't understand why we can get value=64
        #  only 3 bits : bits 3-7 seem to be unspecified (upto 2015?)

        if scanning_code != 128:
            raise TranslationError(
                f"Unsupported scanning mode: scanningMode={scanning_code}"
            )

        res_comp_flags = section2["resolutionAndComponentFlags"]
        # res_comp_flags &= 1 | 2 | 16
        # TODO: AGAIN don't understand why we can get value=64
        #  only 4 bits : bits 3-4 and 6-7 unspecified (upto 2015?)

        if res_comp_flags != 128:
            raise TranslationError(
                f"Unsupported grid format: resolutionAndComponentFlags={scanning_code}"
            )

        nlats = section2["Nj"]
        y0 = 0.001 * section2["latitudeOfFirstGridPoint"]
        dy = 0.001 * section2["jDirectionIncrement"]
        y_points = np.arange(nlats, dtype=np.float64) * dy + y0
        dim_coords_and_dims.append(
            (
                DimCoord(
                    y_points,
                    yconame,
                    units="degrees",
                    coord_system=coord_system,
                ),
                0,
            )
        )

        nlons = section2["Ni"]
        x0 = 0.001 * section2["longitudeOfFirstGridPoint"]
        dx = 0.001 * section2["iDirectionIncrement"]
        x_points = np.arange(nlons, dtype=np.float64) * dx + x0
        dim_coords_and_dims.append(
            (
                DimCoord(
                    x_points,
                    xconame,
                    units="degrees",
                    coord_system=coord_system,
                ),
                1,
            )
        )
    if grid_name in ("latlon", "rotated_latlon"):


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
    # convert_time(field, metadata)
    #
    # vertical layer definition :  mostly section 2
    # convert_vertical(field, metadata)

    # horizontal grid :  mostly section 2
    # N.B. this one **has** to take "field", so we can still use computed keys (yuck!)
    convert_horizontal(field, metadata)
