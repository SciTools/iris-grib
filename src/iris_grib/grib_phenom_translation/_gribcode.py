# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Provide object to represent grib phenomena.

For use as cube attributes, freely convertible to+from strings
"""

from __future__ import annotations
from dataclasses import dataclass
import re


def _invalid_edition(edition):
    msg = f"Invalid grib edition, {edition!r}, for GRIBcode : " "can only be 1 or 2."
    raise ValueError(msg)


def _invalid_nargs(args):
    nargs = len(args)
    msg = (
        f"Cannot create GRIBCode from {nargs} arguments, "
        f"GRIBCode({args!r}) : expects either 1 or 4 arguments."
    )
    raise ValueError(msg)


# Regexp to extract four integers from a string:
# - for four times ...
# - match any non-digits (including none) and discard
# - then match any digits (including none), and return as a "group"
_RE_PARSE_FOURNUMS = re.compile(4 * r"[^\d]*(\d*)")


def _fournums_from_gribcode_string(grib_param_string):
    parsed_ok = True
    # get the numbers..
    match_groups = _RE_PARSE_FOURNUMS.match(grib_param_string).groups()
    # N.B. always produces 4 "strings of digits", but some can be empty
    try:
        nums = [int(grp) for grp in match_groups]
    except ValueError:
        parsed_ok = False

    if not parsed_ok:
        msg = (
            "Invalid argument for GRIBCode creation, "
            '"GRIBCode({!r})" : '
            "requires 4 numbers, separated by non-numerals."
        )
        raise ValueError(msg.format(grib_param_string))

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
        _invalid_nargs(())

    # Convert single argument to *args
    if not args and not kwargs:
        # Convert to a string and extract 4 integers.
        # NOTE: this also allows input from a GRIBCode, or a plain tuple.
        edition_string = str(edition)
        edition, arg2, arg3, arg4 = _fournums_from_gribcode_string(edition_string)
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
        kwargs["edition"] = edition
    else:
        # Include edition, which just makes it simpler
        args = tuple([edition] + list(args))
        nargs = len(args)
        if nargs != 4:
            _invalid_nargs(args)

        for i_arg, (arg, name) in enumerate(
            zip(args, instance_cls.argnames, strict=False)
        ):
            if name in kwargs:
                msg = (
                    f"Keyword {name!r}={kwargs[name]!r} "
                    f"is not compatible with a {i_arg + 1}th argument."
                )
                raise ValueError(msg)
            else:
                kwargs[name] = arg

    result = instance_cls(**kwargs)
    return result


@dataclass
class GenericConcreteGRIBCode:
    """
    Common behaviour for GRIBCode1 and GRIBCode2.

    GRIBCode1 and GRIBCode2 inherit this, making both dataclasses.
    They contain different data properties.
    """

    def __init__(self, **kwargs):
        # Note : only support creation with kargs.  In GRIBCode(), any args
        #  get translated into kwargs
        # Check against "_edition", defined by the specific subclass.
        assert kwargs["edition"] == self._edition
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _broken_repr(self):
        result = (
            f"<{self.__class__.__name__} with invalid content: " f"{self.__dict__}>"
        )
        return result

    def __str__(self):
        edition = self.edition
        try:
            # NB fallback to "invalid" if edition not one of (1, 2)
            format = {
                1: "GRIB{:1d}:t{:03d}c{:03d}n{:03d}",
                2: "GRIB{:1d}:d{:03d}c{:03d}n{:03d}",
            }[edition]
            arg_values = [getattr(self, argname) for argname in self.argnames]
            # NB fallback to "invalid" if format fails
            result = format.format(*arg_values)
        except Exception:
            # Invalid content somewhere : fall back on default repr
            result = self._broken_repr()

        return result

    def __repr__(self):
        edition = self.edition
        try:
            assert edition in (1, 2)
            key_value_strings = []
            for argname in self.argnames:
                value = getattr(self, argname, None)
                assert isinstance(value, int)
                key_value_strings.append(f"{argname}={value}")
            inner_text = ", ".join(key_value_strings)
            result = f"GRIBCode({inner_text})"
        except Exception:
            # Invalid content somewhere : fall back on a default repr
            result = self._broken_repr()

        return result


class GRIBCode1(GenericConcreteGRIBCode):
    edition: int = 1
    table_version: int | None = None
    centre_number: int | None = None
    number: int | None = None
    argnames = ["edition", "table_version", "centre_number", "number"]
    _edition = 1  # Constructor argument should always match this


class GRIBCode2(GenericConcreteGRIBCode):
    edition: int = 2
    discipline: int | None = None
    category: int | None = None
    number: int | None = None
    argnames = ["edition", "discipline", "category", "number"]
    _edition = 2  # Constructor argument should always match this
