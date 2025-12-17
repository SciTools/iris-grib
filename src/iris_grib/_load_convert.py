# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Module to support loading of GRIB data.

Code to convert a GRIB GribMessage or GribWrapper into cube metadata.

"""

from argparse import Namespace
from collections import OrderedDict

from iris.exceptions import TranslationError
from iris.fileformats.rules import ConversionMetadata


options = Namespace(warn_on_unsupported=False, support_hindcast_values=True)


def convert(field):
    """
    Translate the GRIB message into the appropriate cube metadata.

    Args:

    * field:
        GRIB message to be translated.

    Returns:
        A :class:`iris.fileformats.rules.ConversionMetadata` object.

    """
    from ._grib1_legacy.grib1_load_rules import grib1_convert as old_grib1_convert  # noqa: PLC0415
    from ._grib2_convert import grib2_convert  # noqa: PLC0415

    if hasattr(field, "sections"):
        editionNumber = field.sections[0]["editionNumber"]

        if editionNumber != 2:
            emsg = "GRIB edition {} is not supported by {!r}."
            raise TranslationError(emsg.format(editionNumber, type(field).__name__))

        # Initialise the cube metadata.
        metadata = OrderedDict()
        metadata["factories"] = []
        metadata["references"] = []
        metadata["standard_name"] = None
        metadata["long_name"] = None
        metadata["units"] = None
        metadata["attributes"] = {}
        metadata["cell_methods"] = []
        metadata["dim_coords_and_dims"] = []
        metadata["aux_coords_and_dims"] = []

        # Convert GRIB2 message to cube metadata.
        grib2_convert(field, metadata)

        result = ConversionMetadata._make(metadata.values())
    else:
        editionNumber = field.edition

        if editionNumber != 1:
            emsg = "GRIB edition {} is not supported by {!r}."
            raise TranslationError(emsg.format(editionNumber, type(field).__name__))

        result = old_grib1_convert(field)

    return result
