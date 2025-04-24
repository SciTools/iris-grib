.. iris-grib documentation master file, created by
   sphinx-quickstart on Fri May 13 11:48:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root ``toctree`` directive.

Iris-grib v0.20
===============

The library ``iris-grib`` provides functionality for converting between weather and
climate datasets that are stored as GRIB files and Iris :class:`~iris.cube.Cube`\s.
GRIB files can be loaded as Iris cubes using ``iris-grib`` so that you can use Iris
for analysing and visualising the contents of the GRIB files. Iris cubes can also be
saved to GRIB edition-2 files using ``iris-grib``.


Simple GRIB Loading and Saving with Iris
----------------------------------------
You can use the functionality provided by ``iris-grib`` directly within Iris
without having to explicitly import ``iris-grib``, as long as you have both Iris
and ``iris-grib`` installed in your Python environment.

**This is the preferred route if no special control is required.**

.. testsetup::

   import iris
   import iris_grib
   import warnings

   warnings.simplefilter("ignore")
   cube = iris.load_cube(iris.sample_data_path("rotated_pole.nc"))
   iris.save(cube, "testfile.grib", saver="grib2")

For example, to load GRIB data :

    >>> cube = iris.load_cube('testfile.grib')

Similarly, you can save cubes to a GRIB file directly from Iris :

    >>> iris.save(cube, 'my_file.grib2')

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

* ``"GRIB1:t002c007n033"`` is GRIB1 with table2Version=2, centre=7
  ("US National Weather Service - NCEP (WMC)"), and indicatorOfParameter=33
  ("U-component of wind m s**-1").

  * This translates to a standard_name and units of "x_wind / m s-1".

Parameter saving control
^^^^^^^^^^^^^^^^^^^^^^^^
When a cube has a ``GRIB_PARAM`` attribute, as described above, this controls what the
relevant message keys are set to on saving.
(N.B. at present applies only to GRIB2, since we don't support GRIB1 saving)


Iris-grib Load and Save API
---------------------------
In addition to direct load and save with Iris, as described above,
it is also possible to load and save GRIB data using iris-grib functions.

Loading and saving Cubes
^^^^^^^^^^^^^^^^^^^^^^^^
Load
~~~~
To load from a GRIB file with ``iris-grib``, you can call the
:func:`~iris_grib.load_cubes` function :

    >>> cubes_iter = iris_grib.load_cubes('testfile.grib')
    >>> print(cubes_iter)
    <generator object load_cubes at ...>

As we can see, this returns a generator object. The generator object may be iterated
over to access all the Iris cubes loaded from the GRIB file, or converted directly
to a list::

    >>> cubes = list(cubes_iter)
    >>> print(cubes)
    [<iris 'Cube' of air_temperature / (K) (projection_y_coordinate: 200; projection_x_coordinate: 247)>]

In effect, this is the same as using ``iris.load_raw(...)``.
So, in most cases, **that is preferable.**

Save
~~~~
To use ``iris-grib`` to save Iris cubes to a GRIB file we can make use of the
:func:`~iris_grib.save_grib2` function :

    >>> iris_grib.save_grib2(cube, 'my_file.grib2')

In effect, this is the same as using ``iris.save(cube, ...)``.
So, in most cases, **that is preferable.**


Working with GRIB messages
^^^^^^^^^^^^^^^^^^^^^^^^^^
Iris-grib also provides lower-level functions which allow the user to inspect and
adjust actual GRIB encoding details, for precise custom control of loading and saving.

These functions use intermediate objects which represent individual GRIB file
"messages", with all the GRIB metadata.

For example:

* correct loading of some messages with incorrectly encoded parameter number
* save messages with adjusted parameter encodings
* load messages with an unsupported parameter definition template : adjust them to
  mimic a similar type which *is* supported by cube translation, and post-modify the
  resulting cubes to correct the Iris metadata

You can load and save messages to and from files, and convert them to and from Cubes.

.. note::
    at present this only works with GRIB2 data.

.. note::
    Messages are not represented in the same way for loading and saving : the messages
    generated by loading *from* files are represented by
    :class:`iris_grib.message.GribMessage` objects, whereas messages generated from
    cubes, for saving *to* files, are represented as message handles from the
    `Python eccodes library <https://confluence.ecmwf.int/display/ECC/Python+3+interface+for+ecCodes>`_ .

Load
~~~~
The key functions are :func:`~iris_grib.load_pairs_from_fields` and
:func:`~iris_grib.message.GribMessage.messages_from_filename`.
See those for more detail.

You can load data to 'messages', and filter or modify them to enable or correct
how Iris converts them to 'raw' cubes (i.e. individual 2-dimensional fields).

For example:

   >>> from iris_grib.message import GribMessage
   >>> fields_iter = GribMessage.messages_from_filename('testfile.grib')
   >>> # select only wanted data
   >>> selected_fields = [
   ...   field
   ...   for field in fields_iter
   ...   if field.sections[4]['parameterNumber'] == 33
   ... ]
   >>> cube_field_pairs = iris_grib.load_pairs_from_fields(selected_fields)

Filtering fields can be very useful to speed up loading, since otherwise all data must
be converted to Iris *before* selection with constraints, which can be quite costly.


Save
~~~~
The key functions are :func:`~iris_grib.save_pairs_from_cubes` and
:func:`~iris_grib.save_messages`.
See those for more detail.

You can convert Iris cubes to eccodes messages, and modify or filter them before saving.

.. note::
   The messages here are eccodes message "ids", essentially integers, and *not*
   :class:`~iris_grib.message.GribMessages`.  Thus, they must be inspected and
   manipulated using the eccodes library functions.

.. testsetup::

   from iris.coords import DimCoord
   import eccodes

   cube_height_2m5 = iris.load_cube(iris.sample_data_path("rotated_pole.nc"))
   cube_height_2m5.add_aux_coord(DimCoord([2.5], standard_name="height", units="m"), ())

For example:

  >>> # translate data to grib2 fields
  >>> cube_field_pairs = list(iris_grib.save_pairs_from_cube(cube_height_2m5))
  >>> # adjust some of them
  >>> for cube, field in cube_field_pairs:
  ...   if cube.coords('height') and cube.coord('height').points[0] == 2.5:
  ...     # we know this will have been rounded, badly, so needs re-scaling.
  ...     assert eccodes.codes_get_long(field, 'scaleFactorOfFirstFixedSurface') == 0
  ...     assert eccodes.codes_get_long(field, 'scaledValueOfFirstFixedSurface') == 2
  ...     eccodes.codes_set_long(field, 'scaleFactorOfFirstFixedSurface', 1)
  ...     eccodes.codes_set_long(field, 'scaledValueOfFirstFixedSurface', 25)
  ...
  >>> # save to file
  >>> messages = [msg for (cube, msg) in cube_field_pairs]
  >>> iris_grib.save_messages(messages, 'temp.grib2')
  >>> # check result
  >>> print(iris.load_cube('temp.grib2').coord('height').points)
  [2.5]


Getting Started
===============

To ensure all ``iris-grib`` dependencies, it is sufficient to have installed
:mod:`Iris <iris>` itself, and
`ecCodes <https://confluence.ecmwf.int/display/ECC/ecCodes+Home>`_ .

The simplest way to install is with
`conda <https://conda.io/miniconda.html>`_ , using the
`package on conda-forge <https://anaconda.org/conda-forge/iris-grib>`_ ,
with the command::

   $ conda install -c conda-forge iris-grib

Pip can also be used, to install from the
`package on PyPI <https://pypi.org/project/iris-grib/>`_ ,
with the command::

   $ pip install iris-grib

Development sources are hosted at `<https://github.com/SciTools/iris-grib>`_ .

Releases
========

For recent changes, see :ref:`release_notes` .


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
