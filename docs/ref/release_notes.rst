What's new in iris-grib v0.13
=============================

:Release: 0.13.0
:Date: T.B.D.

Features
--------

* Added saving of data on Hybrid Pressure levels (surface type 119 in
  code table 4.5).

* Added loading and saving of data on Hybrid Height levels (surface type 118 in
  code table 4.5).

Bug Fixes
---------

* Fixed a bug with loading data on Hybrid Pressure levels (surface types 105
  and 119 in code table 4.5).  
  Previously, *all* hybrid coordinate values, in both 'level_pressure' and
  'sigma' coordinates, were loaded from the next level up,
  i.e. (model_level_number + 1).

  .. note::

      This changes loading behaviour for data on hybrid pressure levels only.
      This is an incompatible change, but the coefficent values previously
      returned were essentially useless, with some values missing.


What's new in iris-grib v0.12
=============================

:Release: 0.12
:Date: 25 Oct 2017

Updated to work with
`ecCodes <https://software.ecmwf.int/wiki/display/ECC/ecCodes+Home>`_ as its
interface to GRIB files.
This is ECMWF's replacement for the older GRIB-API, which is now deprecated.


What's new in iris-grib v0.11
=============================

:Release: 0.11
:Date: 25 Oct 2017

Update for Iris v2.0+, using `dask <https://dask.pydata.org>`_ in place of
`biggus <https://github.com/SciTools/biggus>`_ for deferred loading.


What's new in iris-grib v0.9
=============================

:Release: 0.9.0
:Date: 25 Jul 2016

Stable release of iris-grib to support iris v1.10

