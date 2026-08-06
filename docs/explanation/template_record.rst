.. _template_record:

Template Recording
==================

Overview
--------

The :data:`~iris_grib.TEMPLATE_RECORD` object is a control which enables the recording
of GRIB2 **grid definition template numbers** during loading :  which are then added as
an extra attribute of loaded cubes.  The presence of this ``GRIB2_GRID_TEMPLATE``
attribute can subsequently influence how data is is saved back to a GRIB2 format file.


What is a Grid Definition Template?
-----------------------------------

In GRIB2 messages, the **Grid Definition Section (Section 3)** describes how the
data is laid out geographically. The type of grid is specified by a
**grid definition template number** (from GRIB2 Code Table 3.1).

Templates supported by iris-grib include:

- **GDT 3.0**: Regular latitude/longitude grid
- **GDT 3.1**: Rotated latitude/longitude grid
- **GDT 3.4**: Variable resolution latitude/longitude
- **GDT 3.5**: Variable resolution rotated latitude/longitude
- **GDT 3.10**: Mercator projection
- **GDT 3.20**: Polar stereographic
- **GDT 3.30**: Lambert conformal
- **GDT 3.40**: Gaussian grid

For most regular rectangular grids, the template is inferred automatically from
the coordinate structure during saving. However, for specialized grids, **notably
Gaussian grids (template GDT 3.40)**, the structure is more complex and cannot be
reliably inferred from the coordinate metadata alone.


The TEMPLATE_RECORD Control
---------------------------

The ``TEMPLATE_RECORD`` control is essentially like a boolean flag, which can be set to
either ``True`` or ``False`` to enable or disable the recording of the template number
in cubes loaded from GRIB2 data.

When enabled, the template number is stored as a
``GRIB2_GRID_TEMPLATE`` attribute.  It is **disabled by default**.

To enable template recording during loading, use one of these methods:

.. testsetup::

    from pathlib import Path
    from iris.config import TEST_DATA_DIR

    grib_data_dir = Path(TEST_DATA_DIR) / "GRIB"


**Method 1: Context manager (for temporary use)**

.. doctest::

    >>> from iris_grib import TEMPLATE_RECORD
    >>> import iris
    >>> testpath = grib_data_dir / "lambert" / "lambert.grib2"

    >>> with TEMPLATE_RECORD.context(record=True):
    ...     cube1 = iris.load_cube(testpath)
    ...     print(cube1.attributes.get("GRIB2_GRID_TEMPLATE", None))
    ...
    30

    # Template recording is automatically disabled after the context block
    >>> cube2 = iris.load_cube(testpath)
    >>> print(cube2.attributes.get("GRIB2_GRID_TEMPLATE", None))
    None

**Method 2: Persistent setting**

.. doctest::

    >>> # Enable template recording for all subsequent loads
    >>> TEMPLATE_RECORD.set(True)

    >>> cube = iris.load_cube(grib_data_dir / "reduced" / "reduced_gg.grib2")
    >>> print(cube.attributes.get("GRIB2_GRID_TEMPLATE", None))
    40


.. testcleanup::

    # Make sure is reset to default (off) after doctests
    TEMPLATE_RECORD.set(False)


The ``GRIB2_GRID_TEMPLATE`` attribute
-------------------------------------
This attribute, when present, shows the exact type of source grid used in the GRIB2
message(s) from which a cube was loaded.

In principle, it can also be used to determine how data is saved to GRIB2 format,
i.e. with what Grid Definition Template.  Currently, however, this **only** affects the
saving to reduced gaussian grids (GDT 3.40) -- see below.

This attribute can also be added by the user, to control the output format.
For example, reduced-gaussian data loaded from GRIB1 messages (which do not have a grid
definition template like GRIB2 data) can be saved to GRIB2 with the correct template by
adding the attribute manually :

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import iris

    # source data is on a gaussian grid, defined by GRIB1 messages
    cube = iris.load_cube("data.grib1")
    # as not GRIB2 data, does not get a GRIB2_GRID_TEMPLATE attribute
    # but as we know this is appropriate, we can add it manually.
    cube.attributes["GRIB2_GRID_TEMPLATE"] = 40
    iris.save(cube, "data.grib2")
    # Data is saved with GDT 3.40


Template 3.40: Gaussian Grids
-----------------------------

Template 3.40 represents data on a **Gaussian grid**. This grid structure:

-   Uses Gaussian latitude points (not regular spacing)

-   May have *either* "regular" or "reduced" longitudes:

    -   "regular" grids have a fixed set of longitude points, the same for all latitudes

    -   "reduced" grids have varying numbers of longitude points at different latitudes

Loading
^^^^^^^
Iris-grib can load data from either of these types of grid, but the resulting cubes have
different coordinate structures.

-   "reduced" grids have a single grid dimension, shared by both the latitude and
    longitude coordinates. In the case of GRIB2 data, this dimension also has an
    identifying dimension coordinate called ``gaussian_grid``.

-   "regular" grids have two separate latitude and longitude dimensions, and coordinates,
    i.e. the same longitude points at each latitude.  The data is a corresponding 2D
    mesh of points.  Such cubes are essentially the same as data loaded from
    'irregular' lat-lon grids (which is GDT 3.4 in GRIB2 data).

Saving
^^^^^^
When saving data to GRIB2, the grid definition template is inferred from the coordinate
structure.

-   "Reduced" gaussian-grid data **can not be saved without** the appropriate
    ``GRIB2_GRID_TEMPLATE = 40`` attribute.  If the structure of the latitudes and
    longitudes is consistent with a GDT3.40 reduced Gaussian grid, then it will be saved
    as such.  If the attribute is missing, or different, or if the coordinate structure
    is wrong, an error will be raised :  It is not (currently) possible to save data on
    a 1-dimensional grid in any other way.

-   "Regular" gaussian-grid data, however, can currently only be saved as an
    "irregular lat-lon" grid (GDT 3.4).  In future, it may be possible to save this as
    GDT 3.40, but this is **not currently implemented**.


Related Concepts
----------------

-   **GRIB Parameter Records**: Similar to template records, the ``GRIB_PARAM``
    attribute records the original parameter encoding. See
    :doc:`phenom_translation` for details.

-   **Reduced Gaussian Grids**: Common in climate models; learn more about
    Gaussian quadrature and reduced Gaussian grids in atmospheric modelling
    documentation. See
    `OpenIFS: Gaussian grids <https://confluence.ecmwf.int/spaces/OIFS/pages/85396207/4.1+OpenIFS+Gaussian+grids>`_.


Summary
-------

-   Use ``TEMPLATE_RECORD.set(True)`` or ``TEMPLATE_RECORD.context(record=True)``
    to record grid definition templates during loading

-   The recorded template is stored as a ``GRIB2_GRID_TEMPLATE`` cube attribute

-   The special ``GRIB2_GRID_TEMPLATE`` attribute can also in some cases control *how*
    data is saved -- notably for certain specialized grids, such as the Gaussian grids

    -   A ``GRIB2_GRID_TEMPLATE`` attribute can also be **written by the user** to enable
        saving data in a particular form

-   The special attribute is **required** to save data to a reduced Gaussian grid format
    (GDT 3.40), otherwise the save will raise an error.

    -   This can be used to successfully save reduced gaussian grids loaded from GRIB1
        data to GRIB2 format (since iris-grib cannot save to GRIB1).
