Release Notes
=============


What's new in iris-grib v0.19.0
-------------------------------

:Release: 0.19.0
:Date: [unreleased]


=======
Features
^^^^^^^^
* `@lbdreyer <https://github.com/lbdreyer>`_ and 
  `@pp-mo <https://github.com/pp-mo>`_ (reviewer) modified the loading of GRIB
  messages with an unrecognised fixed surface type. These are now loaded in as
  an unnamed coordinate with an attribute called GRIB_fixed_surface_type.
  iris-grib will also save out cubes with this attribute as the given fixed
  surface type.`(PR#318) <https://github.com/SciTools/iris-grib/pull/288>`_


Bugs Fixed
^^^^^^^^^^
* `@lbdreyer <https://github.com/lbdreyer>`_ and
  `@pp-mo <https://github.com/pp-mo>`_ (reviewer) modified the GRIB1 loading
  code so that it no longer assumes a spherical Earth with radius of 6371229 m
  and instead uses the resolutionAndComponentFlag to determine the shape of the
  Earth. This can either be a spherical Earth with radius of 6367470 m or an
  oblate spheroid, the latter of which is not supported. Note that this change
  in Earth's radius will result in a different coordinate system and may also
  affect the coordinate values.
  `(PR#316) <https://github.com/SciTools/iris-grib/pull/316>`_


Dependencies
^^^^^^^^^^^^
* now requires Python version >= 3.9


What's new in iris-grib v0.18.0
-------------------------------

:Release: 0.18.0
:Date: 14 March 2022

Bugs Fixed
^^^^^^^^^^
* `@lbdreyer <https://github.com/lbdreyer>`_ made various updates to allow
  iris-grib to work with the latest versions of
  `iris <https://scitools-iris.readthedocs.io/en/stable/>`_,
  `cf-units <https://cf-units.readthedocs.io/en/latest/>`_,
  `ecCodes <https://software.ecmwf.int/wiki/display/ECC/ecCodes+Home>`_ and
  `cartopy <https://scitools.org.uk/cartopy/docs/latest/>`_, including casting
  the usage of :meth:`cf_units.Unit.date2num` as float. setting and setting the
  values of some missing keys using ``gribapi.GRIB_MISSING_LONG``.
  `(PR#288) <https://github.com/SciTools/iris-grib/pull/288>`_


Dependencies
^^^^^^^^^^^^
* now requires Python version >= 3.8


Internal
^^^^^^^^
* `@TomDufall <https://github.com/TomDufall>`_ updated the code so that it was
  `flake8 <https://flake8.pycqa.org/en/stable/>`_ compliant and enabled flake8
  checks to the CI.
  `(PR#271) <https://github.com/SciTools/iris-grib/pull/271>`_


What's new in iris-grib v0.17.1
-------------------------------

:Release: 0.17.1
:Date: 8 June 2021

Bugs Fixed
^^^^^^^^^^

* `@TomDufall <https://github.com/TomDufall>`_ removed the empty slice
  handling (originally added in v0.15.1) as this used
  iris.util._array_slice_ifempty which was removed in Iris v3.0.2 and is no
  longer necessary.
  `(PR#270) <https://github.com/SciTools/iris-grib/pull/270>`_


Dependencies
^^^^^^^^^^^^

* now requires Iris version >= 3.0.2.

* now requires Python version >= 3.7.



What's new in iris-grib v0.17
-----------------------------

:Release: 0.17.0
:Date: 18 May 2021

Features
^^^^^^^^

* `@m1dr <https://github.com/m1dr>`_ added support for GRIB regulation 92.1.8
  for loading GRIB files where the longitude increment is not given.
  `(PR#261) <https://github.com/SciTools/iris-grib/pull/261>`_

* `@lbdreyer <https://github.com/lbdreyer>`_ added support for loading grid
  point and spectral data with CCSDS recommended lossless compression, i.e.
  data representation template 42.
  `(PR#264) <https://github.com/SciTools/iris-grib/pull/264>`_


Internal
^^^^^^^^

* `@jamesp <https://github.com/jamesp>`_ moved CI testing to Cirrus CI.
  `(PR#250) <https://github.com/SciTools/iris-grib/pull/250>`_



What's new in iris-grib v0.16
-----------------------------

:Release: 0.16.0
:Date: 27 Jan 2021

Features
^^^^^^^^

* `@tpowellmeto <https://github.com/tpowellmeto>`_ added support for loading
  data on a "Lambert Azimuthal Equal Area Projection",
  i.e. grid definition template 3.140.
  `(PR#187) <https://github.com/SciTools/iris-grib/pull/187>`_

* `@bjlittle <https://github.com/bjlittle>`_ made all the tests runnable for a
  packaged install of iris-grib, where the grib testdata files will be missing.
  `(PR#212) <https://github.com/SciTools/iris-grib/pull/212>`_

* `@m1dr <https://github.com/m1dr>`_ added support for loading statistical
  fields, as encoded in production definition template 3.8, even when the
  "interval time increment" value is not specified (i.e. set to "missing").
  `(PR#206) <https://github.com/SciTools/iris-grib/pull/206>`_

* `@pp-mo <https://github.com/pp-mo>`_ ported some tests from Iris, which test
  grib saving of data loaded from other formats.
  `(PR#213) <https://github.com/SciTools/iris-grib/pull/213>`_

* All grib-dependent testing is now contained in iris-grib : **There are no
  remaining tests in Iris which use grib.**


Bugs Fixed
^^^^^^^^^^

* `@lbdreyer <https://github.com/lbdreyer>`_ unpinned the python-eccodes
  version for Travis testing, and added a workaround for a known bug in recent
  versions of python-eccodes.
  Previously, we could only test against python-eccodes versions ">=0.9.1,<2".
  `(PR#208) <https://github.com/SciTools/iris-grib/pull/208>`_

* `@pp-mo <https://github.com/pp-mo>`_ fixed save operations to round off the
  the integer values of vertical surfaces, instead of truncating them.
  `(PR#210) <https://github.com/SciTools/iris-grib/pull/210>`_

* `@pp-mo <https://github.com/pp-mo>`_ fixed loading of grid definition
  template 3.90, "Space view perspective or orthographic grid", which was
  **broken since Iris 2.3**.  This now produces data with an iris
  `Geostationary <https://scitools-iris.readthedocs.io/en/latest/generated/api/iris/coord_systems.html#iris.coord_systems.Geostationary>`_
  coordinate system.  Prior to Iris 2.3, what is now the Iris 'Geostationary'
  class was (incorrectly) named "VerticalPerspective" :  When that was
  `corrected in Iris 2.3 <https://github.com/SciTools/iris/pull/3406>`_ , it
  broke the iris-grib loading, since the data was now incorrectly
  assigned the "new-style" Iris
  `VerticalPerspective <https://scitools-iris.readthedocs.io/en/latest/generated/api/iris/coord_systems.html#iris.coord_systems.VerticalPerspective>`_
  coordinate system, equivalent to the Cartopy
  `NearsidePerspective <https://scitools.org.uk/cartopy/docs/latest/crs/projections.html#nearsideperspective>`_
  and Proj
  `"nsper" <https://proj.org/operations/projections/nsper.html>`_ .
  The plotting behaviour of this is now **the same again as before Iris 2.3** :
  only the Iris coordinate system has changed.
  `(PR#223) <https://github.com/SciTools/iris-grib/pull/223>`_

* `@pp-mo <https://github.com/pp-mo>`_ fixed a problem where cubes were loading from GRIB 1 with a changed coordinate
  system, since eccodes versions >= 1.19.  This resulted from a change to eccodes, which now returns a different
  'shapeOfTheEarth' parameter : see `eccodes issue ECC-811 <https://jira.ecmwf.int/browse/ECC-811>`_ .  This resulted
  in a coordinate system with a different earth radius.
  For backwards compatibilty, the earth radius has now been fixed to the same value as previously.
  However, pending further investigation, this value may be technically incorrect and we may
  yet decide to change it in a future release.
  `(PR#240) <https://github.com/SciTools/iris-grib/pull/240>`_


Dependencies
^^^^^^^^^^^^

* now requires Iris version >= 3.0
  Needed for the bugfix in
  `PR#223 <https://github.com/SciTools/iris-grib/pull/223>`_ .



What's new in iris-grib v0.15.1
-------------------------------

:Release: 0.15.1
:Date: 24 Feb 2020

Bugs Fixed
^^^^^^^^^^

* `@pp-mo <https://github.com/pp-mo>`_ fixed a problem that caused very slow
  loading, and possible memory overflows, with Dask versions >= 2.0.
  **This requires Iris >= 2.4**, as a new minimum dependency.
  ( This problem was shared with UM file access in Iris : see
  https://scitools.org.uk/iris/docs/v2.4.0/whatsnew/2.4.html#bugs-fixed ).
  `(PR#190) <https://github.com/SciTools/iris-grib/pull/190>`_

* `@trexfeathers <https://github.com/trexfeathers>`_ fixed all the tests to
  work with the latest Iris version, previously broken since Iris >= 2.3.
  `(PR#184) <https://github.com/SciTools/iris-grib/pull/184>`_
  and `(PR#185) <https://github.com/SciTools/iris-grib/pull/185>`_

* `@lbdreyer <https://github.com/lbdreyer>`_ fixed a problem with the metadata
  in setup.py.
  `(PR#183) <https://github.com/SciTools/iris-grib/pull/183>`_


Internal
^^^^^^^^

* `@lbdreyer <https://github.com/lbdreyer>`_ and
  `@pp-mo <https://github.com/pp-mo>`_ ported various grib-specific tests from
  Iris.
  ( `PR#191 <https://github.com/SciTools/iris-grib/pull/191>`_ ,
  `PR#192 <https://github.com/SciTools/iris-grib/pull/192>`_ ,
  `PR#194 <https://github.com/SciTools/iris-grib/pull/194>`_ ,
  `PR#195 <https://github.com/SciTools/iris-grib/pull/195>`_ ,
  `PR#198 <https://github.com/SciTools/iris-grib/pull/198>`_ ,
  `PR#199 <https://github.com/SciTools/iris-grib/pull/199>`_ ,
  `PR#200 <https://github.com/SciTools/iris-grib/pull/200>`_ ,
  `PR#201 <https://github.com/SciTools/iris-grib/pull/201>`_  and
  `PR#203 <https://github.com/SciTools/iris-grib/pull/203>`_ )

Dependencies
^^^^^^^^^^^^

* now requires Iris version >= 2.4
  Needed for the bugfix in
  `PR#190 <https://github.com/SciTools/iris-grib/pull/190>`_ .


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
