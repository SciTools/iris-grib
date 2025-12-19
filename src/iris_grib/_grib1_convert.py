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
import eccodes

import numpy as np
from iris.coord_systems import CoordSystem

from iris.coords import DimCoord
from iris import coord_systems
from iris.exceptions import TranslationError
from iris.fileformats.rules import (
    ConversionMetadata,
)

from iris_grib.message import GribMessage, Section
from iris_grib import grib_phenom_translation as gptx

# _CENTRE_NAME_NUMBERS_BACKREFS = {
#     "egrr": 74,
#     "ecmwf": 98,
# }


def phenomenon(field: GribMessage, metadata: ConversionMetadata):
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


def decode_coords(section2: Section) -> (np.ndarray, np.ndarray):
    scanning_mode = section2["scanningMode"]
    # Extract the only bit which we understand (for now)
    y_negative = (scanning_mode & 64) != 0
    if (scanning_mode & ~64) != 0:
        msg = f"Unsupported scanning mode: scanningMode=0b{scanning_mode:0b8}"
        raise TranslationError(msg)
    # Now get the X and Y points arrays.
    # Note that we need to support 'reduced' grids, which are not totally irregular, but
    #  have numbers of points in a row differing at different

    if Ni == "missing":
        row_lengths = section2["pl"]
        xvals = np.array([], dtype=np.float64)

    # NOTE: gaussian grids -- it's really complex
    #  see: https://github.com/ecmwf/eccodes/blob/2.44.2/src/eccodes/geo/grib_geography.cc#L97
    # ALSO
    # in these cases, we have a 'iDirectionIncrement' but NO 'jDirectionIncrement'
    #  - that's a bit hint!


@dataclasses.dataclass
class _CoordInfo:
    coord_system: CoordSystem
    xvals: np.ndarray
    yvals: np.ndarray


def decode_coord_system(section2: Section) -> _CoordInfo:
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
        coord_system = coord_systems.GeogCS(semi_major_axis=6367470)

    if grid_name == "rotated_latlon":
        spole_lon = 0.001 * section2["longitudeOfSouthernPole"]
        spole_lat = 0.001 * section2["latitudeOfSouthernPole"]
        rot_ang = section2["angleOfRotationInDegrees"]
        geoid = coord_systems.GeogCS(semi_major_axis=6367470)
        coord_system = coord_systems.RotatedGeogCS(
            -spole_lat,
            (spole_lon + 180.0) % 360.0,
            ellipsoid=coord_system,
        )

    xvals, yvals = decode_coords(section2)
    if grid_name == "latlon":
        xname, yname = "longitude", "latitude"
    elif grid_name == "rotated_latlon":
        xname, yname = "grid_longitude", "grid_latitude"
    else:
        xname, yname = "projection_x_coordinate", "projection_y_coordinate"

    return result


def horizontal(section2: Section, metadata: ConversionMetadata):
    grid_type = section2["dataRepresentationType"]
    dim_coords_and_dims = metadata["dim_coords_and_dims"]
    match grid_type:
        case 10:
            # rotated latitude-longitude

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

            spole_lon = 0.001 * section2["longitudeOfSouthernPole"]
            spole_lat = 0.001 * section2["latitudeOfSouthernPole"]
            rot_ang = section2["angleOfRotationInDegrees"]
            geoid = coord_systems.GeogCS(semi_major_axis=6367470)
            coord_system = coord_systems.RotatedGeogCS(
                -spole_lat,
                (spole_lon + 180.0) % 360.0,
                rot_ang,
                geoid,
            )

            nlats = section2["Nj"]
            y0 = 0.001 * section2["latitudeOfFirstGridPoint"]
            dy = 0.001 * section2["jDirectionIncrement"]
            y_points = np.arange(nlats, dtype=np.float64) * dy + y0
            dim_coords_and_dims.append(
                (
                    DimCoord(
                        y_points,
                        "grid_latitude",
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
                        "grid_longitude",
                        units="degrees",
                        coord_system=coord_system,
                    ),
                    1,
                )
            )

        case _:
            msg = (
                "Unsupported grid type in grib message: "
                f"dataRepresentationType={grid_type}"
            )
            raise TranslationError(msg)


def grib1_convert(field: GribMessage, metadata: ConversionMetadata):
    assert hasattr(field, "sections")
    assert field.sections[0]["editionNumber"] == 1

    # Section 1 == product definitions
    phenomenon(field, metadata)
    horizontal(field.sections[2], metadata)
