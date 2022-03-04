# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
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
import re
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

_Grib1ToCfKeyClass = namedtuple(
    'Grib1CfKey',
    ('table2_version', 'centre_number', 'param_number'))

# NOTE: this form is currently used for both Grib1 *and* Grib2
_GribToCfDataClass = namedtuple(
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
        grib1_key = _Grib1ToCfKeyClass(table2_version=int(table2_version),
                                       centre_number=int(centre_number),
                                       param_number=int(param_number))
        if standard_name is not None:
            if standard_name not in iris.std_names.STD_NAMES:
                warnings.warn('{} is not a recognised CF standard name '
                              '(skipping).'.format(standard_name))
                return None
        # convert units string to iris Unit (i.e. mainly, check it is good)
        a_cf_unit = cf_units.Unit(units)
        cf_data = _GribToCfDataClass(standard_name=standard_name,
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

_Grib2ToCfKeyClass = namedtuple(
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
        grib2_key = _Grib2ToCfKeyClass(param_discipline=int(param_discipline),
                                       param_category=int(param_category),
                                       param_number=int(param_number))
        if standard_name is not None:
            if standard_name not in iris.std_names.STD_NAMES:
                warnings.warn('{} is not a recognised CF standard name '
                              '(skipping).'.format(standard_name))
                return None
        # convert units string to iris Unit (i.e. mainly, check it is good)
        a_cf_unit = cf_units.Unit(units)
        cf_data = _GribToCfDataClass(standard_name=standard_name,
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

_CfToGrib2KeyClass = namedtuple(
    'CfGrib2Key',
    ('standard_name', 'long_name'))

_CfToGrib2DataClass = namedtuple(
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
        cf_key = _CfToGrib2KeyClass(standard_name, long_name)
        # convert units string to iris Unit (i.e. mainly, check it is good)
        a_cf_unit = cf_units.Unit(units)
        grib2_data = _CfToGrib2DataClass(discipline=int(param_discipline),
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
    grib1_key = _Grib1ToCfKeyClass(table2_version=table2_version,
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
    grib2_key = _Grib2ToCfKeyClass(param_discipline=int(param_discipline),
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


class GRIBCode(namedtuple('GRIBCode',
                          'edition discipline category number')):
    """
    An object representing a specific Grib phenomenon identity.

    Basically a namedtuple of (edition, discipline, category, number).

    Also provides a string representation, and supports creation from: another
    similar object; a tuple of numbers; or any string with 4 separate decimal
    numbers in it.

    """
    __slots__ = ()

    def __new__(cls, edition_or_string,
                discipline=None, category=None, number=None):
        args = (edition_or_string, discipline, category, number)
        nargs = sum(arg is not None for arg in args)
        if nargs == 1:
            # Single argument: convert to a string and extract 4 integers.
            # NOTE: this also allows input from a GRIBCode, or a plain tuple.
            edition_or_string = str(edition_or_string)
            edition, discipline, category, number = \
                cls._fournums_from_gribcode_string(edition_or_string)
        elif nargs == 4:
            edition = edition_or_string
            edition, discipline, category, number = [
                int(arg)
                for arg in (edition, discipline, category, number)]
        else:
            msg = ('Cannot create GRIBCode from {} arguments, '
                   '"GRIBCode{!r}" : '
                   'expected either 1 or 4 non-None arguments.')
            raise ValueError(msg.format(nargs, args))

        return super(GRIBCode, cls).__new__(
            cls, edition, discipline, category, number)

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

    PRINT_FORMAT = 'GRIB{:1d}:d{:03d}c{:03d}n{:03d}'

    def __str__(self):
        result = self.PRINT_FORMAT.format(
            self.edition, self.discipline, self.category, self.number)
        return result
