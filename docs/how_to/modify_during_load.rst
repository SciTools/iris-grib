How to modify GRIB content during loading
=========================================

See also: :doc:`/tutorial/load_save_api`.

.. testsetup::

    import iris
    import warnings

    warnings.simplefilter("ignore")
    cube = iris.load_cube(iris.sample_data_path("A1B_north_america.nc"))
    cube.coord("forecast_period").guess_bounds()
    filename = "test_file.grib"
    iris.save(cube, filename, saver="grib2")

Here is a basic example of how you can modify the GRIB messages being loaded,
and how to turn those modified messages into Iris cubes.

    >>> import iris
    >>> from iris.cube import CubeList
    >>> from iris_grib import GribMessage, load_pairs_from_fields
    >>>
    >>> def adjust_message(msg: GribMessage) -> GribMessage:
    ...     # Advance all time steps by 1 hour.
    ...     if msg.sections[0]["editionNumber"] == 2:
    ...         s1 = msg.sections[1]
    ...         s1["hour"] += 1
    ...         s4 = msg.sections[4]
    ...         s4["hourOfEndOfOverallTimeInterval"] += 1
    ...     return msg

    >>> original = iris.load_cube(filename)
    >>> fields = GribMessage.messages_from_filename(filename)
    >>> fields = (adjust_message(msg) for msg in fields)
    >>> cubes = CubeList(cube for cube, _ in load_pairs_from_fields(fields))
    >>> modified = cubes.combine_cube()

Compare the final 5 time steps of the original and modified cubes:

    >>> print(original.coord("time").points[-5:])
    [1084524. 1093236. 1101936. 1110636. 1119336.]
    >>> print(modified.coord("time").points[-5:])
    [1084525. 1093237. 1101937. 1110637. 1119337.]
