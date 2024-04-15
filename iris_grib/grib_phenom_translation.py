# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
'''
Provide grib 1 and 2 phenomenon translations to + from CF terms.

This is done by wrapping '_grib_cf_map.py',
which is in a format provided by the metadata translation project.


Currently supports only these ones:

* grib1 --> cf
* grib2 --> cf
* cf --> grib2

'''
from collections import namedtuple
from dataclasses import dataclass
import re
from typing import Optional
import warnings

import cf_units

from . import _grib_cf_map as grcf
import iris.std_names


class _LookupTable(dict):
    """
    Specialised dictionary object for making lookup tables.

    Returns None for unknown keys (instead of raising exception).
    Raises exception for any attempt to change an existing entry,
    (but it is still possible to remove keys)

    """
    def __init__(self, *args, **kwargs):
        self._super = super()
        self._super.__init__(*args, **kwargs)

    def __getitem__(self, key):
        if key not in self:
            return None
        return self._super.__getitem__(key)

    def __setitem__(self, key, value):
        if key in self and self[key] is not value:
            raise KeyError('Attempted to set dict[{}] = {}, '
                           'but this is already set to {}.'.format(
                               key, value, self[key]))
        self._super.__setitem__(key, value)


# Define namedtuples for keys+values of the Grib1 lookup table.

Grib1CfKey = namedtuple(
    'Grib1CfKey',
    ('table2_version', 'centre_number', 'param_number'))

# NOTE: this form is currently used for both Grib1 *and* Grib2
Grib1CfData = namedtuple(
    'Grib1CfData',
    ('standard_name', 'long_name', 'units', 'set_height'))


# Create the grib1-to-cf lookup table.

def _make_grib1_cf_table():
    """ Build the Grib1 to CF phenomenon translation table. """
    table = _LookupTable()

    def _make_grib1_cf_entry(table2_version, centre_number, param_number,
                             standard_name, long_name, units, set_height=None):
        """
        Check data, convert types and create a new _GRIB1_CF_TABLE key/value.

        Note that set_height is an optional parameter.  Used to denote
        phenomena that imply a height definition (agl),
        e.g. "2-metre tempererature".

        """
        grib1_key = Grib1CfKey(table2_version=int(table2_version),
                               centre_number=int(centre_number),
                               param_number=int(param_number))
        if standard_name is not None:
            if standard_name not in iris.std_names.STD_NAMES:
                warnings.warn('{} is not a recognised CF standard name '
                              '(skipping).'.format(standard_name))
                return None
        # convert units string to iris Unit (i.e. mainly, check it is good)
        a_cf_unit = cf_units.Unit(units)
        cf_data = Grib1CfData(standard_name=standard_name,
                              long_name=long_name,
                              units=a_cf_unit,
                              set_height=set_height)
        return (grib1_key, cf_data)

    # Interpret the imported Grib1-to-CF table.
    for (grib1data, cfdata) in grcf.GRIB1_LOCAL_TO_CF.items():
        assert grib1data.edition == 1
        association_entry = _make_grib1_cf_entry(
            table2_version=grib1data.t2version,
            centre_number=grib1data.centre,
            param_number=grib1data.iParam,
            standard_name=cfdata.standard_name,
            long_name=cfdata.long_name,
            units=cfdata.units)
        if association_entry is not None:
            key, value = association_entry
            table[key] = value

    # Do the same for special Grib1 codes that include an implied height level.
    for (grib1data, (cfdata, extra_dimcoord)) \
            in grcf.GRIB1_LOCAL_TO_CF_CONSTRAINED.items():
        assert grib1data.edition == 1
        if extra_dimcoord.standard_name != 'height':
            raise ValueError('Got implied dimension coord of "{}", '
                             'currently can only handle "height".'.format(
                                 extra_dimcoord.standard_name))
        if extra_dimcoord.units != 'm':
            raise ValueError('Got implied dimension units of "{}", '
                             'currently can only handle "m".'.format(
                                 extra_dimcoord.units))
        if len(extra_dimcoord.points) != 1:
            raise ValueError('Implied dimension has {} points, '
                             'currently can only handle 1.'.format(
                                 len(extra_dimcoord.points)))
        association_entry = _make_grib1_cf_entry(
            table2_version=int(grib1data.t2version),
            centre_number=int(grib1data.centre),
            param_number=int(grib1data.iParam),
            standard_name=cfdata.standard_name,
            long_name=cfdata.long_name,
            units=cfdata.units,
            set_height=extra_dimcoord.points[0])
        if association_entry is not None:
            key, value = association_entry
            table[key] = value

    return table


_GRIB1_CF_TABLE = _make_grib1_cf_table()


# Define a namedtuple for the keys of the Grib2 lookup table.

Grib2CfKey = namedtuple(
    'Grib2CfKey',
    ('param_discipline', 'param_category', 'param_number'))


# Create the grib2-to-cf lookup table.

def _make_grib2_to_cf_table():
    """ Build the Grib2 to CF phenomenon translation table. """
    table = _LookupTable()

    def _make_grib2_cf_entry(param_discipline, param_category, param_number,
                             standard_name, long_name, units):
        """
        Check data, convert types and make a _GRIB2_CF_TABLE key/value pair.

        Note that set_height is an optional parameter.  Used to denote
        phenomena that imply a height definition (agl),
        e.g. "2-metre tempererature".

        """
        grib2_key = Grib2CfKey(param_discipline=int(param_discipline),
                               param_category=int(param_category),
                               param_number=int(param_number))
        if standard_name is not None:
            if standard_name not in iris.std_names.STD_NAMES:
                warnings.warn('{} is not a recognised CF standard name '
                              '(skipping).'.format(standard_name))
                return None
        # convert units string to iris Unit (i.e. mainly, check it is good)
        a_cf_unit = cf_units.Unit(units)
        cf_data = Grib1CfData(standard_name=standard_name,
                              long_name=long_name,
                              units=a_cf_unit,
                              set_height=None)
        return (grib2_key, cf_data)

    # Interpret the grib2 info from grib_cf_map
    for grib2data, cfdata in grcf.GRIB2_TO_CF.items():
        assert grib2data.edition == 2
        association_entry = _make_grib2_cf_entry(
            param_discipline=grib2data.discipline,
            param_category=grib2data.category,
            param_number=grib2data.number,
            standard_name=cfdata.standard_name,
            long_name=cfdata.long_name,
            units=cfdata.units)
        if association_entry is not None:
            key, value = association_entry
            table[key] = value

    return table


_GRIB2_CF_TABLE = _make_grib2_to_cf_table()


# Define namedtuples for key+values of the cf-to-grib2 lookup table.

CfGrib2Key = namedtuple(
    'CfGrib2Key',
    ('standard_name', 'long_name'))

CfGrib2Data = namedtuple(
    'CfGrib2Data',
    ('discipline', 'category', 'number', 'units'))


# Create the cf-to-grib2 lookup table.

def _make_cf_to_grib2_table():
    """ Build the Grib1 to CF phenomenon translation table. """
    table = _LookupTable()

    def _make_cf_grib2_entry(standard_name, long_name,
                             param_discipline, param_category, param_number,
                             units):
        """
        Check data, convert types and make a new _CF_TABLE key/value pair.

        """
        assert standard_name is not None or long_name is not None
        if standard_name is not None:
            long_name = None
            if standard_name not in iris.std_names.STD_NAMES:
                warnings.warn('{} is not a recognised CF standard name '
                              '(skipping).'.format(standard_name))
                return None
        cf_key = CfGrib2Key(standard_name, long_name)
        # convert units string to iris Unit (i.e. mainly, check it is good)
        a_cf_unit = cf_units.Unit(units)
        grib2_data = CfGrib2Data(discipline=int(param_discipline),
                                 category=int(param_category),
                                 number=int(param_number),
                                 units=a_cf_unit)
        return (cf_key, grib2_data)

    # Interpret the imported CF-to-Grib2 table into a lookup table
    for cfdata, grib2data in grcf.CF_TO_GRIB2.items():
        assert grib2data.edition == 2
        a_cf_unit = cf_units.Unit(cfdata.units)
        association_entry = _make_cf_grib2_entry(
            standard_name=cfdata.standard_name,
            long_name=cfdata.long_name,
            param_discipline=grib2data.discipline,
            param_category=grib2data.category,
            param_number=grib2data.number,
            units=a_cf_unit)
        if association_entry is not None:
            key, value = association_entry
            table[key] = value

    return table


_CF_GRIB2_TABLE = _make_cf_to_grib2_table()


# Interface functions for translation lookup

def grib1_phenom_to_cf_info(table2_version, centre_number, param_number):
    """
    Lookup grib-1 parameter --> cf_data or None.

    Returned cf_data has attributes:

    * standard_name
    * long_name
    * units : a :class:`cf_units.Unit`
    * set_height :  a scalar 'height' value , or None

    """
    grib1_key = Grib1CfKey(table2_version=table2_version,
                           centre_number=centre_number,
                           param_number=param_number)
    return _GRIB1_CF_TABLE[grib1_key]


def grib2_phenom_to_cf_info(param_discipline, param_category, param_number):
    """
    Lookup grib-2 parameter --> cf_data or None.

    Returned cf_data has attributes:

    * standard_name
    * long_name
    * units : a :class:`cf_units.Unit`

    """
    grib2_key = Grib2CfKey(param_discipline=int(param_discipline),
                           param_category=int(param_category),
                           param_number=int(param_number))
    return _GRIB2_CF_TABLE[grib2_key]


def cf_phenom_to_grib2_info(standard_name, long_name=None):
    """
    Lookup CF names --> grib2_data or None.

    Returned grib2_data has attributes:

    * discipline
    * category
    * number
    * units : a :class:`cf_units.Unit`
        The unit represents the defined reference units for the message data.

    """
    if standard_name is not None:
        long_name = None
    return _CF_GRIB2_TABLE[(standard_name, long_name)]


@dataclass
class GRIBCode:
    edition: Optional[int] = None
    grib1_table2_version: Optional[int] = None
    grib1_centre_number: Optional[int] = None
    grib2_discipline: Optional[int] = None
    grib2_parameter_category: Optional[int] = None
    parameter_number: Optional[int] = None

    """
    An object representing a specific Grib phenomenon identity.

    Basically a namedtuple of (edition, discipline, category, number).

    Also provides a string representation, and supports creation from: another
    similar object; a tuple of numbers; or any string with 4 separate decimal
    numbers in it.

    TODO: reorganise into 2 separate dataclasses with different members
    """
    @staticmethod
    def _invalid_edition(edition):
        msg = (
            f"Invalid grib edition, {edition!r}, for GRIBcode : "
            "can only be 1 or 2."
        )
        raise ValueError(msg)

    @staticmethod
    def _invalid_nargs(args):
        nargs = len(args)
        msg = (
            f"Cannot create GRIBCode from {nargs} arguments, "
            f"GRIBCode({args!r}) : expects either 1 or 4 arguments."
        )
        raise ValueError(msg)

    def __init__(self, edition, *args, **kwargs):
        if edition is None:
            self._invalid_nargs([])

        # Convert single argument to *args
        if not args and not kwargs:
            # Convert to a string and extract 4 integers.
            # NOTE: this also allows input from a GRIBCode, or a plain tuple.
            edition_string = str(edition)
            edition, arg2, arg3, arg4 = \
                self._fournums_from_gribcode_string(edition_string)
            args = [arg2, arg3, arg4]

        # Check edition + assign relevant keywords
        if edition == 1:
            argnames = [
                "grib1_table2_version",
                "grib1_centre_number",
                "parameter_number"
            ]
        elif edition == 2:
            argnames = [
                "grib2_discipline",
                "grib2_parameter_category",
                "parameter_number",
            ]
        else:
            self._invalid_edition(edition)

        # Convert *args to *kwargs
        if args:
            if len(args) != 3:
                nargs = len(args) + 1
                args = tuple([edition] + list(args))
                msg = (
                    f"Cannot create GRIBCode from {nargs} arguments, "
                    f"GRIBCode({args!r}) : expects either 1 or 4 arguments."
                )
                raise ValueError(msg.format(nargs, edition, args))

            for i_arg, (arg, name) in enumerate(zip(args, argnames)):
                if name in kwargs:
                    msg = (
                        f"Keyword {name!r}={kwargs[name]!r} "
                        "is not compatible with a {i_arg + 1}th argument."
                    )
                    raise ValueError(msg)
                else:
                    kwargs[name] = arg

        # Check + assign the properties relevant to the edition
        self.edition = edition
        for arg_name in argnames:
            value = kwargs.get(arg_name, None)
            if value is None:
                msg = (
                    "Missing required argument or keyword:"
                    f"GRIBcode(edition={edition}) must have a value "
                    f"for {arg_name!r}."
                )
                raise ValueError(msg)
            setattr(self, arg_name, int(value))

    RE_PARSE_FOURNUMS = re.compile(4 * r'[^\d]*(\d*)')

    @classmethod
    def _fournums_from_gribcode_string(cls, edcn_string):
        parsed_ok = False
        nums_match = cls.RE_PARSE_FOURNUMS.match(edcn_string).groups()
        if nums_match is not None:
            try:
                nums = [int(grp) for grp in nums_match]
                parsed_ok = True
            except ValueError:
                pass

        if not parsed_ok:
            msg = ('Invalid argument for GRIBCode creation, '
                   '"GRIBCode({!r})" : '
                   'requires 4 numbers, separated by non-numerals.')
            raise ValueError(msg.format(edcn_string))

        return nums

    def __str__(self):
        if self.edition == 1:
            format = 'GRIB1:t{:03d}c{:03d}n{:03d}'
            result = format.format(
                self.grib1_table2_version,
                self.grib1_centre_number,
                self.parameter_number
            )
        elif self.edition == 2:
            format = 'GRIB2:d{:03d}c{:03d}n{:03d}'
            result = format.format(
                self.grib2_discipline,
                self.grib2_parameter_category,
                self.parameter_number
            )
        else:
            self._invalid_edition(self.edition)

        return result
