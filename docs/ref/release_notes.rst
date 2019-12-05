Release Notes
=============

What's new in iris-grib v0.15
-----------------------------

:Release: 0.15.0
:Date: 5 Dec 2019

Features
^^^^^^^^

* Updated translations between GRIB parameter code and CF standard_name or
  long_name :
      * additional WAFC codes, both to and from CF
      * 'mass_fraction_of_cloud_liquid_water_in_air' and 'mass_fraction_of_cloud_ice_in_air', both to and from CF
      * 'surface_downwelling_longwave_flux_in_air', now translates to GRIBcode(2, 0, 5, 3)  (but not the reverse).
      * for full details, see : https://github.com/Scitools/iris-grib/compare/c4243ae..5c314e3#diff-cf46b46880cae59e82a91c7ab6bb81ba

* Added support for loading GRIB messages with no fixed surface set in the
  product definition section

* Added support for loading GRIB messages where i or j increment are not set

* Added support for saving cubes that have a "depth" coordinate

* Cubes loaded from GRIB files now contain a new GRIB_PARAM attribute, the
  value of which is an instance of
  iris_grib.grib_phenom_translation.GRIBCode and represents the parameter code.
  When saving, if a cube has a GRIBCode attribute, this determines the parameter code
  in the created message(s): This will _override_ any translation from the CF names.
  
Bug Fixes
^^^^^^^^^

* Reverted a bug that was fixed in v0.13 related to loading hybrid pressure 
  levels. It was agreed that the initial behaviour was correct 

Dependencies
^^^^^^^^^^^^

* Python 2 is no longer supported


What's new in iris-grib v0.14
-----------------------------

:Release: 0.14.0
:Date: 6 Mar 2019

Features
^^^^^^^^

* Added support for WAFC aviation codes.

* Added loading and saving of statistically processed values over a spatial
  area at a horizontal level or in a horizontal layer at a point in time
  (product definition template 15 in code table 4.0)

:Release: 0.14.1
:Date: 12 Jun 2019

Bug Fixes
^^^^^^^^^

* Added fixes to get iris-grib working with the Python 3 compatible release of
  eccodes. This included workarounds such that lists that are returned by
  eccodes are converted to NumPy arrays as expected.


What's new in iris-grib v0.13
-----------------------------

:Release: 0.13.0
:Date: 15 Jun 2018

Features
^^^^^^^^

* Added saving of data on Hybrid Pressure levels (surface type 119 in
  code table 4.5).

* Added loading and saving of data on Hybrid Height levels (surface type 118 in
  code table 4.5).

* Added loading and saving of data using Mercator projection (grid definition
  template 10 in template table 3.1)

  .. note::

      Loading and saving for the Mercator projection is only available using
      iris versions greater than 2.1.0.

* Added saving for data on irregular, non-rotated grids (grid definition
  template 4 in template table 3.1)

* Added release notes for versions since 0.9.


Bug Fixes
^^^^^^^^^

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
-----------------------------

:Release: 0.12
:Date: 25 Oct 2017

Updated to work with
`ecCodes <https://software.ecmwf.int/wiki/display/ECC/ecCodes+Home>`_ as its
interface to GRIB files.
This is ECMWF's replacement for the older GRIB-API, which is now deprecated.


What's new in iris-grib v0.11
-----------------------------

:Release: 0.11
:Date: 25 Oct 2017

Update for Iris v2.0+, using `dask <https://dask.pydata.org>`_ in place of
`biggus <https://github.com/SciTools/biggus>`_ for deferred loading.


What's new in iris-grib v0.9
-----------------------------

:Release: 0.9.0
:Date: 25 Jul 2016

Stable release of iris-grib to support iris v1.10
