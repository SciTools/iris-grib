:orphan:

.. _release_notes:

Release Notes
=============


What's new in iris-grib v0.21.0
-------------------------------

:Release: 0.21.0
:Date: [unreleased]

Features
^^^^^^^^

* `@trexfeathers <https://github.com/trexfeathers>`_ added checks for invalid
  values in the following keys when loading grid definition template 3.10
  (mercator grids): ``orientationOfTheGrid``, ``longitudeOfLastGridPoint``,
  ``latitudeOfLastGridPoint``.
  `(ISSUE#118) <https://github.com/SciTools/iris-grib/issues/118>`_,
  `(PR#446) <https://github.com/SciTools/iris-grib/pull/446>`_


Bugs Fixed
^^^^^^^^^^

* N/A


Documentation
^^^^^^^^^^^^^

* N/A


Dependencies
^^^^^^^^^^^^

* N/A


Internal
^^^^^^^^

* N/A


New Contributors
^^^^^^^^^^^^^^^^

* N/A


What's new in iris-grib v0.20.0
-------------------------------

:Release: 0.20.0
:Date: 29 August 2024

Features
^^^^^^^^
* `@abooton <https://github.com/abooton>`_ added support for saving data on a
  Lambert Azimuthal Equal Area (LAEA) projection, as grid definition template 3.140.
  `(ISSUE#344) <https://github.com/SciTools/iris-grib/issues/344>`_,
  `(PR#343) <https://github.com/SciTools/iris-grib/pull/343>`_

* `@trexfeathers <https://github.com/trexfeathers>`_,
  `@mo-marqh <https://github.com/mo-marqh>`_  and
  `@pp-mo <https://github.com/pp-mo>`_ added support for production definition template
  4.6, i.e. percentile forecasts.
  `(PR#401) <https://github.com/SciTools/iris-grib/pull/401>`_,
  `(PR#295) <https://github.com/SciTools/iris-grib/pull/295>`_,
  `(PR#271) <https://github.com/SciTools/iris-grib/pull/271>`_

* `@pp-mo <https://github.com/pp-mo>`_ expanded the use of the "GRIB_PARAM"
  attributes to GRIB1 loading, and documented it more thoroughly.
  `(ISSUE#330) <https://github.com/SciTools/iris-grib/issues/330>`_,
  `(PR#402) <https://github.com/SciTools/iris-grib/pull/402>`_

* `@DPeterK <https://github.com/DPeterK>`_ and
  `@trexfeathers <https://github.com/trexfeathers>`_ added saving support for
  grid definition template 20 - polar stereographic.
  `(ISSUE#122) <https://github.com/SciTools/iris-grib/issues/122>`_,
  `(PR#405) <https://github.com/SciTools/iris-grib/pull/405>`_


Documentation
^^^^^^^^^^^^^
* `@tkknight <https://github.com/tkknight>`_ fixed docs building on ReadTheDocs, and
  enabled a test docs-build for each individual PR.
  `(ISSUE#365) <https://github.com/SciTools/iris-grib/issues/365>`_,
  `(PR#366) <https://github.com/SciTools/iris-grib/pull/366>`_

* `@tkknight <https://github.com/tkknight>`_ made docs builds treat warnings as errors.
  `(PR#471) <https://github.com/SciTools/iris-grib/pull/471>`_

* `@pp-mo <https://github.com/pp-mo>`_ reworked the main docs page to :
  headline basic load + save with Iris, rather than lower-level functions;
  better explain load-pairs and save-pairs usage; make all usage examples into
  doctests.
  `(ISSUE#398) <https://github.com/SciTools/iris-grib/issues/398>`_,
  `(PR#402) <https://github.com/SciTools/iris-grib/pull/402>`_

* `@bjlittle <https://github.com/bjlittle>`_ updated the readme, replacing README.rst
  with README.md and adding a logo .
  `(PR#440) <https://github.com/SciTools/iris-grib/pull/440>`_,
  `(PR#447) <https://github.com/SciTools/iris-grib/pull/447>`_

* `@tkknight <https://github.com/tkknight>`_ fixed the display formatting of linux
  commands.
  `(PR#455) <https://github.com/SciTools/iris-grib/pull/455>`_


Dependencies
^^^^^^^^^^^^
* `@pp-mo <https://github.com/pp-mo>`_ enabled support for
  `eccodes v2.36 <https://confluence.ecmwf.int/display/ECC/ecCodes+version+2.36.0+released>`_.
  Eccodes v2.36 has implemented some backwards incompatible changes :
  The ``indicatorOfUnitOfTimeRange`` key was removed, to be replaced with
  ``indicatorOfUnitForForecastTime`` (but only in GRIB v2 messages, not GRIB 1);
  and the ``iScansPositively`` and ``jScansPositively`` keys became read-only.
  The resulting changes mean **we now only support eccodes >=2.33**.
  `(PR#504) <https://github.com/SciTools/iris-grib/issues/504>`_

* `@bjlittle <https://github.com/bjlittle>`_ added iris-sample-data as a dependency,
  as required for doctests.
  `(PR#413) <https://github.com/SciTools/iris-grib/pull/413>`_

* `@pp-mo <https://github.com/pp-mo>`_ made essential changes for compatibility with
  Iris >= 3.10.
  `(PR#463) <https://github.com/SciTools/iris-grib/pull/463>`_


Internal
^^^^^^^^
* `@trexfeathers <https://github.com/trexfeathers>`_ updated CONTRIBUTING.md in line with the
  newer v5 SciTools CLA. `(PR#371) <https://github.com/SciTools/iris-grib/pull/371>`_

* `@pp-mo <https://github.com/pp-mo>`_ updated an obsolete license header in one test.
  `(PR#374) <https://github.com/SciTools/iris-grib/pull/374>`_

* `@trexfeathers <https://github.com/trexfeathers>`_ and
  `@pp-mo <https://github.com/pp-mo>`_  added a pre-commit configuration and got all
  checks passing.
  `(ISSUE#388) <https://github.com/SciTools/iris-grib/issues/388>`_,
  `(PR#400) <https://github.com/SciTools/iris-grib/pull/400>`_,
  `(PR#406) <https://github.com/SciTools/iris-grib/pull/406>`_

* `@HGWright <https://github.com/HGWright>`_ and
  `@trexfeathers <https://github.com/trexfeathers>`_ replaced setup.py with
  pyproject.toml.
  `(ISSUE#387) <https://github.com/SciTools/iris-grib/issues/387>`_,
  `(PR#408) <https://github.com/SciTools/iris-grib/pull/408>`_,
  `(PR#429) <https://github.com/SciTools/iris-grib/pull/429>`_

* `@stephenworsley <https://github.com/stephenworsley>`_ configured for MyPy checking via
  pre-commit.
  `(ISSUE#386) <https://github.com/SciTools/iris-grib/issues/386>`_,
  `(PR#407) <https://github.com/SciTools/iris-grib/pull/407>`_

* `@ESadek-MO <https://github.com/ESadek-MO>`_ and
  `@bjlittle <https://github.com/bjlittle>`_ migrated CI testing from Cirrus to
  GitHub Actions.
  `(ISSUE#340) <https://github.com/SciTools/iris-grib/issues/340>`_,
  `(PR#415) <https://github.com/SciTools/iris-grib/pull/415>`_,
  `(PR#425) <https://github.com/SciTools/iris-grib/pull/425>`_,
  `(PR#432) <https://github.com/SciTools/iris-grib/pull/432>`_

* `@trexfeathers <https://github.com/trexfeathers>`_ and
  `@HGWright <https://github.com/HGWright>`_ adopted Ruff for code style checking.
  `(ISSUE#384) <https://github.com/SciTools/iris-grib/issues/384>`_,
  `(PR#430) <https://github.com/SciTools/iris-grib/pull/430>`_,
  `(PR#419) <https://github.com/SciTools/iris-grib/pull/419>`_

* `@bjlittle <https://github.com/bjlittle>`_ migrated the test runs from
  nose to pytest.
  `(ISSUE#253) <https://github.com/SciTools/iris-grib/issues/253>`_,
  `(ISSUE#412) <https://github.com/SciTools/iris-grib/issues/412>`_,
  `(PR#420) <https://github.com/SciTools/iris-grib/pull/420>`_,
  `(PR#424) <https://github.com/SciTools/iris-grib/pull/424>`_

* `@stephenworsley <https://github.com/stephenworsley>`_ removed the now-redundant
  _iris_mercator_support.py.
  `(ISSUE#431) <https://github.com/SciTools/iris-grib/issues/431>`_,
  `(PR#433) <https://github.com/SciTools/iris-grib/pull/433>`_,
  `(PR#435) <https://github.com/SciTools/iris-grib/pull/435>`_

* `@bjlittle <https://github.com/bjlittle>`_ added build manifest checking in GHA.
  `(PR#427) <https://github.com/SciTools/iris-grib/pull/427>`_,
  `(PR#436) <https://github.com/SciTools/iris-grib/pull/436>`_,
  `(PR#441) <https://github.com/SciTools/iris-grib/pull/441>`_

* `@bjlittle <https://github.com/bjlittle>`_ added dependabot checking.
  `(PR#426) <https://github.com/SciTools/iris-grib/pull/426>`_

* `@bjlittle <https://github.com/bjlittle>`_ removed 'wheel' dependency from build
  system, as-per
  `repo-review <https://learn.scientific-python.org/development/guides/repo-review/>`_.
  `(PR#437) <https://github.com/SciTools/iris-grib/pull/437>`_

* `@bjlittle <https://github.com/bjlittle>`_ fixed blacken-docs url in pre-commit,
  as per
  `repo-review <https://learn.scientific-python.org/development/guides/repo-review/>`_.
  `(PR#438) <https://github.com/SciTools/iris-grib/pull/438>`_

* `@bjlittle <https://github.com/bjlittle>`_ provided a custom per-commit.ci message,
  as per
  `repo-review <https://learn.scientific-python.org/development/guides/repo-review/>`_.
  `(PR#439) <https://github.com/SciTools/iris-grib/pull/439>`_

* `@pp-mo <https://github.com/pp-mo>`_ removed obsolete workaround routines relating to
  older eccodes versions.
  `(ISSUE#239) <https://github.com/SciTools/iris-grib/issues/239>`_,
  `(PR#410) <https://github.com/SciTools/iris-grib/pull/410>`_

* `@HGWright <https://github.com/HGWright>`_ implemented version handling with
  setuptools.scm .
  `(ISSUE#418) <https://github.com/SciTools/iris-grib/issues/418>`_,
  `(PR#444) <https://github.com/SciTools/iris-grib/pull/444>`_

* `@bjlittle <https://github.com/bjlittle>`_ moved the top-level ``./iris_grib`` folder
  to ``./src/iris_grib``, in line with modern practice, as per
  `repo-review <https://learn.scientific-python.org/development/guides/repo-review/>`_.
  `(ISSUE#421) <https://github.com/SciTools/iris-grib/issues/421>`_,
  `(PR#450) <https://github.com/SciTools/iris-grib/pull/450>`_

* `@bjlittle <https://github.com/bjlittle>`_ adopted .git-blame-ignore-revs to exclude
  some very noisy PRs from file "blame" views
  `(PR#452) <https://github.com/SciTools/iris-grib/pull/452>`_

* `@bjlittle <https://github.com/bjlittle>`_ dropped Python 3.9 support and added 3.12,
  in accordance with `nep29 <https://numpy.org/neps/nep-0029-deprecation_policy.html>`_.
  `(PR#453) <https://github.com/SciTools/iris-grib/pull/453>`_

* `@bjlittle <https://github.com/bjlittle>`_ updated all optional dependency
  requirements, and added codecov support.
  `(PR#454) <https://github.com/SciTools/iris-grib/pull/454>`_,
  `(PR#459) <https://github.com/SciTools/iris-grib/pull/459>`_

* `@bjlittle <https://github.com/bjlittle>`_ added repository health checking with
  `repo-review <https://learn.scientific-python.org/development/guides/repo-review/>`_
  via pre-commit.
  `(ISSUE#392) <https://github.com/SciTools/iris-grib/issues/392>`_,
  `(PR#456) <https://github.com/SciTools/iris-grib/pull/456>`_

* `@bjlittle <https://github.com/bjlittle>`_ added a CODE_OF_CONDUCT.md .
  `(PR#460) <https://github.com/SciTools/iris-grib/pull/460>`_

* `@bjlittle <https://github.com/bjlittle>`_ aligned .gitignore with a suggested
  standard form
  `(PR#461) <https://github.com/SciTools/iris-grib/pull/461>`_

* `@bjlittle <https://github.com/bjlittle>`_ fixed some spelling errors to satisfy
  codespell
  `(PR#479) <https://github.com/SciTools/iris-grib/pull/479>`_

* `@githubalexliu <https://github.com/githubalexliu>`_ fixed a problem with the MyPy
  checking.
  `(ISSUE#496) <https://github.com/SciTools/iris-grib/issues/496>`_,
  `(PR#497) <https://github.com/SciTools/iris-grib/pull/497>`_

* `@trexfeathers <https://github.com/trexfeathers>`_ aligned the pre-commit-config with
  the SciTools "reference" version.
  `(PR#464) <https://github.com/SciTools/iris-grib/pull/464>`_,


New Contributors
^^^^^^^^^^^^^^^^
Welcome to

* `@abooton <https://github.com/abooton>`_
* `@githubalexliu <https://github.com/githubalexliu>`_
* `@stephenworsley <https://github.com/stephenworsley>`_
* `@tkknight <https://github.com/tkknight>`_ fixed the display formatting of linux
* `@DPeterK <https://github.com/DPeterK>`_
* `@ESadek-MO <https://github.com/ESadek-MO>`_
* `@HGWright <https://github.com/HGWright>`_


What's new in iris-grib v0.19.1
-------------------------------

:Release: 0.19.1
:Date: 14 December 2023

Documentation
^^^^^^^^^^^^^
* `@pp-mo <https://github.com/pp-mo>`_ updated the release notes with v0.19 changes.
  `(PR#370) <https://github.com/SciTools/iris-grib/pull/370>`_


What's new in iris-grib v0.19.0
-------------------------------

:Release: 0.19.0
:Date: 16 November 2023

See also :
`GitHub v0.19.0 release page <https://github.com/SciTools/iris-grib/releases/tag/v0.19.0>`_

Features
^^^^^^^^
* `@lbdreyer <https://github.com/lbdreyer>`_ and
  `@pp-mo <https://github.com/pp-mo>`_ (reviewer) modified the loading of GRIB
  messages with an unrecognised fixed surface type. These are now loaded in as
  an unnamed coordinate with an attribute called GRIB_fixed_surface_type.
  iris-grib will also save out cubes with this attribute as the given fixed
  surface type. `(PR#318) <https://github.com/SciTools/iris-grib/pull/318>`_

* `@trexfeathers <https://github.com/trexfeathers>`_ extended Transverse Mercator
  to support negative scanning.
  `(PR#296) <https://github.com/SciTools/iris-grib/pull/296>`_

* `@trexfeathers <https://github.com/trexfeathers>`_  added a number of new GRIB-CF
  mappings, i.e. translations from GRIB parameters to CF standard names and vice-versa.
  `(PR#297) <https://github.com/SciTools/iris-grib/pull/297>`_

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
* `@s-boardman <https://github.com/s-boardman>`_ corrected the calculation of bounded
  forecast periods in GRIB1 loading.
  `(PR#322) <https://github.com/SciTools/iris-grib/pull/322>`_
* `@david-bentley <https://github.com/david-bentley>`_  fixed the calculation of message
  file offsets to work in Windows as well as Linux, which was causing load failures.
  `(PR#287) <https://github.com/SciTools/iris-grib/pull/287>`_
* `@bjlittle <https://github.com/bjlittle>`_  fixed an error that occurred when a
  message had all-missing data points.
  `(PR#362) <https://github.com/SciTools/iris-grib/pull/362>`_


Internal
^^^^^^^^
* `@lbdreyer <https://github.com/lbdreyer>`_ relicensed the repo from LGPL-3 to BSD-3.
  `(PR#359) <https://github.com/SciTools/iris-grib/pull/359>`_

Dependencies
^^^^^^^^^^^^
* now requires Python version >= 3.9
* replaced deprecated eccodes-python PyPI package with new eccodes by @valeriupredoi in #357
* `@valeriupredoi <https://github.com/valeriupredoi>`_ replaced the deprecated
  eccodes-python PyPI package with eccodes.
  `(PR#357) <https://github.com/SciTools/iris-grib/pull/357>`_

New Contributors
^^^^^^^^^^^^^^^^
Welcome to

* `@s-boardman <https://github.com/s-boardman>`_
* `@david-bentley <https://github.com/david-bentley>`_
* `@valeriupredoi <https://github.com/valeriupredoi>`_


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
  `ecCodes <https://confluence.ecmwf.int/display/ECC>`_ and
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
  `Geostationary <https://scitools-iris.readthedocs.io/en/stable/generated/api/iris.coord_systems.html#iris.coord_systems.Geostationary>`_
  coordinate system.  Prior to Iris 2.3, what is now the Iris 'Geostationary'
  class was (incorrectly) named "VerticalPerspective" :  When that was
  `corrected in Iris 2.3 <https://github.com/SciTools/iris/pull/3406>`_ , it
  broke the iris-grib loading, since the data was now incorrectly
  assigned the "new-style" Iris
  `VerticalPerspective <https://scitools-iris.readthedocs.io/en/stable/generated/api/iris.coord_systems.html#iris.coord_systems.VerticalPerspective>`_
  coordinate system, equivalent to the Cartopy
  `NearsidePerspective <https://scitools.org.uk/cartopy/docs/latest/reference/projections.html#nearsideperspective>`_
  and Proj
  `"nsper" <https://proj.org/operations/projections/nsper.html>`_ .
  The plotting behaviour of this is now **the same again as before Iris 2.3** :
  only the Iris coordinate system has changed.
  `(PR#223) <https://github.com/SciTools/iris-grib/pull/223>`_

* `@pp-mo <https://github.com/pp-mo>`_ fixed a problem where cubes were loading from GRIB 1 with a changed coordinate
  system, since eccodes versions >= 1.19.  This resulted from a change to eccodes, which now returns a different
  'shapeOfTheEarth' parameter.  This resulted
  in a coordinate system with a different earth radius.
  For backwards compatibility, the earth radius has now been fixed to the same value as previously.
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
  ( This problem was shared with UM file access in Iris, fixed in Iris 2.4.
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
      This is an incompatible change, but the coefficient values previously
      returned were essentially useless, with some values missing.


What's new in iris-grib v0.12
-----------------------------

:Release: 0.12
:Date: 25 Oct 2017

Updated to work with
`ecCodes <https://confluence.ecmwf.int/display/ECC>`_ as its
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
