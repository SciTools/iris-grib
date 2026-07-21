Template Recording
==================

Overview
--------

The ``TEMPLATE_RECORD`` object is a control which enables the recording of GRIB2
**grid definition template numbers** during loading, which is added as an extra
attribute of loaded cubes.  The presence of this ``GRIB2_GRID_TEMPLATE`` attribute
can subsequently influence how the data is is saved back to a GRIB2 format file.


What is a Grid Definition Template?
-----------------------------------

In GRIB2 files, the **Grid Definition Section (Section 3)** describes how the
data is laid out geographically. The type of grid is specified by a
**grid definition template number** (from GRIB2 Code Table 3.1).

Common templates include:

- **Template 0**: Regular latitude/longitude grid
- **Template 1**: Rotated latitude/longitude grid
- **Template 4**: Variable resolution latitude/longitude
- **Template 5**: Variable resolution rotated latitude/longitude
- **Template 10**: Mercator projection
- **Template 20**: Polar stereographic
- **Template 30**: Lambert conformal
- **Template 40**: Gaussian reduced grid (Gaussian grid on a reduced octahedral mesh)

For most regular rectangular grids, the template is inferred automatically from
the coordinate structure during saving. However, for **specialized grids like
Gaussian grids (Template 40)**, the structure is more complex and cannot be
reliably inferred from the coordinate metadata alone.


The TEMPLATE_RECORD Control
---------------------------

The ``TEMPLATE_RECORD`` control is essential a boolean flag which can be set to either
``True`` or ``False`` to enable or disable the recording of the template number in cubes
loaded from GRIB2 data.

When enabled, the template number is stored as a
``GRIB2_GRID_TEMPLATE`` attribute.  It is **disabled by default**.

To enable template recording during loading, use one of these methods:

**Method 1: Persistent setting**

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import iris

    # Enable template recording for all subsequent loads
    TEMPLATE_RECORD.set(True)

    cube = iris.load_cube("data.grib2")
    print(cube.attributes)
    # Output might include: {'GRIB2_GRID_TEMPLATE': 40, ...}


**Method 2: Context manager (for temporary use)**

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import iris

    with TEMPLATE_RECORD.context(record=True):
        cube = iris.load_cube("data.grib2")
        print(cube.attributes)
        # GRIB2_GRID_TEMPLATE attribute is now available

    # Template recording is automatically disabled after the context block
    cube2 = iris.load_cube("other_data.grib2")
    print("GRIB2_GRID_TEMPLATE" in cube2.attributes)
    # Output: False


The ``GRIB2_GRID_TEMPLATE`` attribute
-------------------------------------
This attribute, when present, shows the exact type of source grid used in the GRIB2 file,
from which a cube was loaded.

When saving certain types of data, it can be used to ensure that the correct grid
definition template is used, matching the original data format.  This is currently
especially useful for **reduced Gaussian grids** (Grid definition template GDT 3.40)
-- see below.

This attribute can also easily be added by the user, to control the output format.
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

Using the Recorded Template for Saving
--------------------------------------

The ``GRIB2_GRID_TEMPLATE`` attribute, when present in a cube, controls how
the cube is saved back to GRIB2 format. This is especially important for
Gaussian reduced grids (Template 40), which require special handling.

**Example: Round-trip with Gaussian grids**

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import iris

    # Load with template recording enabled
    with TEMPLATE_RECORD.context(record=True):
        original_cube = iris.load_cube("gaussian_data.grib2")

    # The cube now has the template attribute
    print(original_cube.attributes["GRIB2_GRID_TEMPLATE"])
    # Output: 40

    # Save the cube - it will use the same template structure
    iris.save(original_cube, "gaussian_data_roundtrip.grib2")

    # Reload and verify
    reloaded_cube = iris.load_cube("gaussian_data_roundtrip.grib2")
    assert reloaded_cube.shape == original_cube.shape
    assert (reloaded_cube.data == original_cube.data).all()


Template 3.40: Gaussian Reduced Grids
-------------------------------------

Template 3.40 represents data on a **Gaussian grid with a reduced octahedral
mesh**. This grid structure:

- Has varying numbers of longitude points at different latitudes
- Uses Gaussian latitude points (not regular spacing)
- Is commonly used in climate and weather models (e.g., ECMWF output)

When ``TEMPLATE_RECORD`` is enabled and a Template 3.40 data file is loaded,
the cube will have ``GRIB2_GRID_TEMPLATE: 40`` in its attributes. This informs
the save mechanism to:

1. Use a special GRIB2 template ("reduced_gg_sfc_grib2") as the base message
2. Apply Template 3.40-specific encoding rules
3. Properly encode the variable longitude counts per latitude (the ``pl`` array)

**Why is this important?**

Without the template attribute, the save mechanism cannot reliably determine
that the data should be encoded as Template 3.40. It would attempt to save using
a standard rectangular grid template, which would fail because:

- Template 3.40 has a different structure with varying longitude counts
- The coordinates are 1-dimensional (not 2D grids with ``x_coord`` and ``y_coord``)

**Example: Template 3.40 specific code**

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import iris
    from iris.coords import DimCoord
    import numpy as np

    # This demonstrates the internal check (for reference)
    # In actual use, this happens automatically when saving

    with TEMPLATE_RECORD.context(record=True):
        cube = iris.load_cube("reduced_gaussian_grid.grib2")

    # Check that the template was recorded
    if cube.attributes.get("GRIB2_GRID_TEMPLATE") == 40:
        print("This is a Gaussian reduced grid")
        print(f"Grid shape: {cube.shape}")
        # The latitude coordinate will have repeated values
        # (one block of longitudes per latitude)


Advanced Usage
--------------

**Examining the TEMPLATE_RECORD state**

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD

    # Check current state
    print(bool(TEMPLATE_RECORD))
    # Output: False (if not recording) or True (if recording enabled)

    print(repr(TEMPLATE_RECORD))
    # Output: TemplateRecorder(_record=False)


**Thread-safe usage**

The ``TEMPLATE_RECORD`` object is thread-local, meaning each thread maintains
its own recording state. This is important for multi-threaded applications:

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import Threading
    import iris


    def load_in_thread(filename):
        # Each thread has its own recording state
        with TEMPLATE_RECORD.context(record=True):
            return iris.load_cube(filename)


    thread = threading.Thread(target=load_in_thread, args=("data.grib2",))
    thread.start()
    # The main thread's TEMPLATE_RECORD state is unaffected


Common Patterns
---------------

**Pattern 1: Load and round-trip test**

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import iris
    import tempfile

    with TEMPLATE_RECORD.context(record=True):
        original = iris.load_cube("input.grib2")

    with tempfile.NamedTemporaryFile(suffix=".grib2") as f:
        iris.save(original, f.name)
        reloaded = iris.load_cube(f.name)
        assert reloaded.shape == original.shape


**Pattern 2: Bulk loading with template preservation**

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import iris
    from pathlib import Path

    # Load all GRIB2 files in a directory, preserving templates
    with TEMPLATE_RECORD.context(record=True):
        cubes = iris.load(str(Path("data") / "*.grib2"))

    # Each cube now has its template information if available
    for cube in cubes:
        if "GRIB2_GRID_TEMPLATE" in cube.attributes:
            template = cube.attributes["GRIB2_GRID_TEMPLATE"]
            print(f"{cube.name()}: Template {template}")


Related Concepts
----------------

- **GRIB Parameter Records**: Similar to template records, the ``GRIB_PARAM``
  attribute records the original parameter encoding. See
  :doc:`phenom_translation` for details.

- **Grid Definition Section**: For technical details on GRIB2 grid definitions,
  consult the `GRIB2 specification <https://www.wmo.int/pages/prog/wis/2010/doc/GRIB2_MASTER_TABLE_283-16-0p1.doc>`_.

- **Reduced Gaussian Grids**: Common in climate models; learn more about
  Gaussian quadrature and reduced Gaussian grids in atmospheric modelling
  documentation.


Troubleshooting
---------------

**Issue: "Expected to find exactly 1 coordinate" error when saving**

This typically occurs when trying to save a Gaussian grid without the template
attribute:

.. code-block:: python

    cube = iris.load_cube("gaussian_data.grib2")  # Loaded without TEMPLATE_RECORD
    iris.save(cube, "output.grib2")
    # Error: CoordinateNotFoundError

**Solution**: Reload with ``TEMPLATE_RECORD`` enabled:

.. code-block:: python

    from iris_grib import TEMPLATE_RECORD
    import iris

    with TEMPLATE_RECORD.context(record=True):
        cube = iris.load_cube("gaussian_data.grib2")
    iris.save(cube, "output.grib2")  # Now works!


**Issue: Attribute is present but not being used during save**

The ``GRIB2_GRID_TEMPLATE`` attribute must be an integer with value ``40``
(or other valid template number). Check:

.. code-block:: python

    cube = iris.load_cube("data.grib2")
    template = cube.attributes.get("GRIB2_GRID_TEMPLATE")
    print(f"Type: {type(template)}, Value: {template}")
    # Must be: Type: <class 'int'>, Value: 40


Summary
-------

- Use ``TEMPLATE_RECORD.set(True)`` or ``TEMPLATE_RECORD.context(record=True)``
  to record grid definition templates during loading
- The recorded template is stored as a ``GRIB2_GRID_TEMPLATE`` cube attribute
- This attribute controls how the cube is saved, ensuring round-trip
  compatibility, especially for specialized grids like Gaussian reduced grids
- Use the context manager method for cleaner, thread-safe code
- Template recording is particularly important when working with Template 3.40
  Gaussian grids
