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

import numpy as np

from iris.coords import DimCoord
from iris import coord_systems
from iris.exceptions import TranslationError
from iris.fileformats.rules import (
    ConversionMetadata,
)

from iris_grib.message import GribMessage
from iris_grib import grib_phenom_translation as gptx

_CENTRE_NAME_NUMBERS_BACKREFS = {
    "egrr": 74,
    "ecmwf": 98,
}


def phenomenon(field: GribMessage, metadata: ConversionMetadata):
    section1 = field.sections[1]

    tables_version = section1["table2Version"]
    centre_name = section1["centre"]
    # It seems that, for GRIB1, we have no access to the original number here.
    centre_number = _CENTRE_NAME_NUMBERS_BACKREFS.get(centre_name, 0)
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


def grid(field: GribMessage, metadata: ConversionMetadata):
    grid_type = field.sections[1]["gridDefinition"]
    section2 = field.sections[2]
    grid_type = section2["dataRepresentationType"]
    dim_coords_and_dims = metadata["dim_coords_and_dims"]
    match grid_type:
        case 10:
            # rotated latitude-longitude

            # just pin this aspect for now
            scanning_code = section2["scanningMode"]
            scanning_code &= 7  # only 3 bits significant??
            # TODO: don't understand why we can get value=64
            #  only 3 bits : bits 3-7 seem to be unspecified (upto 2015?)

            if scanning_code != 0:
                raise TranslationError(
                    f"bad scanning code: scanningMode={scanning_code}"
                )

            res_comp_flags = section2["resolutionAndComponentFlags"]
            res_comp_flags &= 1 | 2 | 16
            # TODO: AGAIN don't understand why we can get value=64
            #  only 4 bits : bits 3-4 and 6-7 unspecified (upto 2015?)

            if res_comp_flags != 0:
                raise TranslationError(
                    f"bad grid scanning: resolutionAndComponentFlags={scanning_code}"
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
    grid(field, metadata)
