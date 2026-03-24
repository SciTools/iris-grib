Simple GRIB Loading and Saving with Iris
========================================

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
