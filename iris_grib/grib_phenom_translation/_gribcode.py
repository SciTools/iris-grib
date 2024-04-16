# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
'''
Provide object to represent grib phenomena

For use as cube attributes, freely convertible to+from strings
'''
from dataclasses import dataclass
import re
from typing import Optional


def _invalid_edition(edition):
    msg = (
        f"Invalid grib edition, {edition!r}, for GRIBcode : "
        "can only be 1 or 2."
    )
    raise ValueError(msg)


def _invalid_nargs(args):
    nargs = len(args)
    msg = (
        f"Cannot create GRIBCode from {nargs} arguments, "
        f"GRIBCode({args!r}) : expects either 1 or 4 arguments."
    )
    raise ValueError(msg)


_RE_PARSE_FOURNUMS = re.compile(4 * r'[^\d]*(\d*)')


def _fournums_from_gribcode_string(edcn_string):
    parsed_ok = False
    nums_match = _RE_PARSE_FOURNUMS.match(edcn_string).groups()
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


def GRIBCode(edition, *args, **kwargs):
    """
    Make an object representing a specific Grib phenomenon identity.

    The class of the result, and the list of its properties, depend on whether
    'edition' is 1 or 2.

    One of :

    * GRIBCode(edition=1, table_version, centre_number, number)
    * GRIBCode(edition=2, discipline, category, number)

    Either provides a string representation, and supports creation from:
    keywords, another similar object; a tuple of numbers; or any string with 4
    separate decimal numbers in it.
    """
    if edition is None:
        _invalid_nargs([])

    # Convert single argument to *args
    if not args and not kwargs:
        # Convert to a string and extract 4 integers.
        # NOTE: this also allows input from a GRIBCode, or a plain tuple.
        edition_string = str(edition)
        edition, arg2, arg3, arg4 = \
            _fournums_from_gribcode_string(edition_string)
        args = [arg2, arg3, arg4]

    # Check edition + select the relevant keywords for the edition
    if edition not in (1, 2):
        _invalid_edition(edition)

    # Choose which actual type we will return.  This also determines the
    # argument (keyword) names.
    instance_cls = {1: GRIBCode1, 2: GRIBCode2}[edition]

    # Convert all of (edition, *args) into **kwargs
    if not args:
        # Ignore that edition= is a required arg -- make it a kwarg
        kwargs['edition'] = edition
    else:
        # Include edition, which just makes it simpler
        args = tuple([edition] + list(args))
        nargs = len(args)
        if nargs != 4:
            msg = (
                f"Cannot create GRIBCode from {nargs} arguments, "
                f"GRIBCode({args!r}) : expects either 1 or 4 arguments."
            )
            raise ValueError(msg.format(nargs, edition, args))

        for i_arg, (arg, name) in enumerate(zip(args, instance_cls.argnames)):
            if name in kwargs:
                msg = (
                    f"Keyword {name!r}={kwargs[name]!r} "
                    "is not compatible with a {i_arg + 1}th argument."
                )
                raise ValueError(msg)
            else:
                kwargs[name] = arg

    result = instance_cls(**kwargs)
    return result


@dataclass
class GenericConcreteGRIBCode:
    def __init__(self, **kwargs):
        # Note : only support creation with kargs.  In GRIBCode(), any args
        #  get translated into kwargs
        assert kwargs['edition'] == self._edition
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        edition = self.edition
        ok_state = edition in (1, 2)
        if ok_state:
            format = {
                1: "GRIB{:1d}:t{:03d}c{:03d}n{:03d}",
                2: "GRIB{:1d}:d{:03d}c{:03d}n{:03d}"
            }[edition]
            arg_values = [
                getattr(self, argname)
                for argname in self.argnames
            ]
            result = format.format(*arg_values)

        else:
            # Invalid content somewhere : fall back on dataclass default repr
            result = super().__str__()

        return result

    def __repr__(self):
        edition = self.edition
        ok_state = edition in (1, 2)
        if ok_state:
            key_value_strings = []
            for argname in self.argnames:
                value = getattr(self, argname, None)
                if not isinstance(value, int):
                    # Unexpected property content : abandon "normal" formatting
                    ok_state = False
                    break
                key_value_strings.append(f"{argname}={value}")
            inner_text = ', '.join(key_value_strings)
            result = f"GRIBCode({inner_text})"

        else:
            # Invalid content somewhere : fall back on dataclass default repr
            result = super().__repr__()

        return result


class GRIBCode1(GenericConcreteGRIBCode):
    edition: int = 1
    table_version: Optional[int] = None
    centre_number: Optional[int] = None
    number: Optional[int] = None
    argnames = ["edition", "table_version", "centre_number", "number"]
    _edition = 1  # Constructor argument should always match this


class GRIBCode2(GenericConcreteGRIBCode):
    edition: int = 2
    discipline: Optional[int] = None
    category: Optional[int] = None
    number: Optional[int] = None
    argnames = ["edition", "discipline", "category", "number"]
    _edition = 2  # Constructor argument should always match this
