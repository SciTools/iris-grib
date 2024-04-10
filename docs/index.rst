.. iris-grib documentation master file, created by
   sphinx-quickstart on Fri May 13 11:48:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Iris-grib v0.20 (unreleased)
============================

The library ``iris-grib`` provides functionality for converting between weather and
climate datasets that are stored as GRIB files and :class:`Iris cubes <iris.cube.Cube>`.
GRIB files can be loaded as Iris cubes using ``iris-grib`` so that you can use Iris
for analysing and visualising the contents of the GRIB files. Iris cubes can be saved to
GRIB files using ``iris-grib``.


Simple GRIB Loading and Saving with Iris
----------------------------------------
You can use the functionality provided by ``iris-grib`` directly within Iris
without having to explicitly import ``iris-grib``, as long as you have both Iris
and ``iris-grib`` available to your Python interpreter.

**This is the preferred route if no special control is required.**

For example, to load GRIB data :

    >>> import iris
    >>> import iris_sample_data
    >>> cube = iris.load_cube(iris.sample_data_path('polar_stereo.grib2'))

Similarly, you can save cubes to a GRIB file directly from Iris :

    >>> iris.save(cubes, 'my_file.grib2')

.. note::
    As the filename suggests, **only saving to GRIB2 is currently supported**.


Phenomenon translation
----------------------
``iris-grib`` attempts to translate between CF phenomenon identities
(i.e. 'standard_name' and possibly 'long_name' attributes), and GRIB parameter codes,
when converting cubes to or from the GRIB format.

A set of tables define known CF translations for GRIB1 and GRIB2 parameters, and can be
interrogated with the functions in :mod:`iris_grib.grib_phenom_translation`.


Parameter loading record
^^^^^^^^^^^^^^^^^^^^^^^^
All cubes loaded from GRIB have a ``GRIB_PARAM`` attribute, which records the parameter
encodings present in the original file message.

Examples :

* ``"GRIB2:d000c003n005"`` represents GRIB2, discipline=0 ("Meteorological products"),
  category=3 ("Mass") and indicatorOfParameter=5 ("Geopotential height (gpm)").

  * This translates to a standard_name and units of "geopotential_height / m"

* ``"GRIB1:d002c007n033"`` is GRIB1 with table2Version=2, centre=7
  ("US National Weather Service - NCEP (WMC)"), and indicatorOfParameter=33
  ("U-component of wind m s**-1").

  * This translates to a standard_name and units of "x_wind / m s-1".

Parameter saving control
^^^^^^^^^^^^^^^^^^^^^^^^
When a cube has a ``GRIB_PARAM`` attribute, as described above, this controls what the
relevant message keys are set to on saving.
(N.B. at present applies only to GRIB2, since we don't support GRIB1 saving)


Specialist Loading and Saving
-----------------------------
In addition to direct load and save with Iris, as described above,
it is also possible to load and save GRIB data using iris-grib functions, which
provides additional control for special cases.

Iris-grib has its own interface for cube loading and saving, and lower-level interfaces
which provide access to details of the specific GRIB metadata encoding.

Loading and saving Cubes
^^^^^^^^^^^^^^^^^^^^^^^^
Load
~~~~
To load from a GRIB file with ``iris-grib``, you can call the
:func:`~iris_grib.load_cubes` function :

    >>> import os
    >>> import iris_sample_data
    >>> import iris_grib
    >>> cubes = iris_grib.load_cubes(os.path.join(iris_sample_data.path,
                                                  'polar_stereo.grib2'))
    >>> print cubes
    <generator object load_cubes at 0x7f69aba69d70>

As we can see, this returns a generator object. The generator object may be iterated
over to access all the Iris cubes loaded from the GRIB file, or converted directly
to a list::

    >>> cubes = list(cubes)
    >>> print cubes
    [<iris 'Cube' of air_temperature / (K) (projection_y_coordinate: 200; projection_x_coordinate: 247)>]

In effect, this is the same as using ``iris.load_raw``.
So, in most cases, **that is preferable.**

Save
~~~~
To use ``iris-grib`` to save Iris cubes to a GRIB file we can make use of the
:func:`~iris_grib.save_grib2` function :

    >>> iris_grib.save_grib2(my_cube, 'my_file.grib2')

In effect, this is the same as using ``iris.save(my_cube, saver='grib2')``.
So, in most cases, **that is preferable.**


Working with GRIB messages
^^^^^^^^^^^^^^^^^^^^^^^^^^
iris-grib also provides intermediate :class:`iris_grib.message.GribMessage` objects,
representing GRIB file "messages" with all the details of the GRIB metadata encoding.
This enables you to adjust or correct GRIB information directly, which is useful in
various cases:

* load data which causes cube translation to fail (error)
* load data with metadata detail which cube translation omits, or misinterprets
* save data with additional metadata or special encodings which cube conversion
  does not support

For example:

* correct loading of some messages with incorrectly encoded parameter number
* load messages with an unsupported parameter definition template : adjust to appear
  as a similar template which cube translation does support, and post-modify the
  resulting cubes to correct the Iris metadata.
* save messages with an adjusted scaling factor of vertical level.

You can load and save ``GribMessage``\s to and from files, and convert them to and from Cubes.

.. note::
    at present this only works with GRIB2 data.

Load
~~~~
The key functions are :func:`~iris_grib.load_pairs_from_fields` and
:func:`~iris_grib.message.GribMessage.messages_from_filename`.
See those for more detail.

You can load data to 'messages', and filter or modify them to enable or correct
how Iris converts them to 'raw' cubes (i.e. individual 2-dimensional fields).

For example:

   >>> from iris_grib.message import GribMessage
   >>> fields_iter = GribMessage.messages_from_filename(filepath)
   >>> # select only wanted data
   >>> selected_fields = [
   ...   field
   ...   for field in fields_iter
   ...   if field..sections[4]['parameterNumber'] == 33
   ... ]
   >>> cube_field_pairs = iris_grib.load_pairs_from_fields(selected_fields)

Filtering fields can be very useful to speed up loading, since otherwise all data must
be converted to Iris *before* selection with constraints, which can be quite costly.


Save
~~~~
The key functions are :func:`~iris_grib.save_pairs_from_cubes` and
:func:`~iris_grib.save_messages`.
See those for more detail.

You can convert Iris cubes to messages, and modify or filter them before saving.

For example:

  >>> # translate data to grib2 fields
  >>> cube_field_pairs = list(iris_grib.save_pairs_from_cube(cube))
  >>> # adjust some of them
  >>> for cube, field in cube_field_pairs:
  ...   if cube.coord('height') and cube.coord('height').points[0] == 2.5:
  ...     # we know this needs scaling, and has been rounded, wrongly
  ...     assert field.sections[4]['scaleFactorOfFirstFixedSurface'] = 0
  ...     field.sections[4]['scaleFactorOfFirstFixedSurface'] = 1
  ...     field.sections[4]['scaledValueOfFirstFixedSurface'] = 25
  ...
  >>> # save to file
  >>> fields = [fld for (fld, cube in cube_field_pairs)]
  >>> iris_grib.save_messages[fields, filename]


Getting Started
===============

To ensure all ``iris-grib`` dependencies, it is sufficient to have installed
:mod:`Iris <iris>` itself, and
`ecCodes <https://software.ecmwf.int/wiki/display/ECC/ecCodes+Home>`_ .

The simplest way to install is with
`conda <https://conda.io/miniconda.html>`_ ,
using the `conda-forge channel <https://anaconda.org/conda-forge>`_ ,
with the command

    $ conda install -c conda-forge iris-grib

Development sources are hosted at `<https://github.com/SciTools/iris-grib>`_ .

Releases
========

For recent changes, see `Release Notes <ref/release_notes.html>`_ .


Indices and tables
==================

Contents:

.. toctree::
   :maxdepth: 3

   ref/iris_grib
   ref/message/message
   ref/grib_phenom_translation/grib_phenom_translation


See also:

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

