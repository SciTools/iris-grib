# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
"""
Integration test for round-trip loading and saving of various grids.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from typing import Literal

import numpy as np
import pytest

from iris import load_cube, save
from iris.coord_systems import GeogCS, PolarStereographic, RotatedGeogCS, Stereographic
from iris.coords import DimCoord
from iris.cube import Cube
from iris.exceptions import CoordinateNotFoundError
from iris.util import is_regular

from iris_grib import TEMPLATE_RECORD
from iris_grib.grib_phenom_translation import GRIBCode
from iris_grib.message import GribMessage


def assert_grib_message_contents(filename, contents):
    for message in GribMessage.messages_from_filename(filename):
        for section, key, expected in contents:
            assert message.sections[section][key] == expected


def test_gdt5_save_load(tmp_path):
    # Load sample UKV data (variable-resolution rotated grid).
    path = tests.get_data_path(("PP", "ukV1", "ukVpmslont.pp"))
    cube = load_cube(path)

    # Extract a single 2D field, for simplicity.
    assert cube.ndim == 3
    assert cube.coord_dims("time") == (0,)
    cube = cube[0]

    # Check that it has a rotated-pole variable-spaced grid, as expected.
    x_coord = cube.coord(axis="x")
    assert isinstance(x_coord.coord_system, RotatedGeogCS)
    assert not is_regular(x_coord)

    temp_file_path = tmp_path / "ukv_sample.grib2"
    save(cube, temp_file_path)

    expect_values = (
        (0, "editionNumber", 2),
        (3, "gridDefinitionTemplateNumber", 5),
        (3, "Ni", cube.shape[-1]),
        (3, "Nj", cube.shape[-2]),
        (3, "shapeOfTheEarth", 6),
        (3, "scaledValueOfRadiusOfSphericalEarth", 0),
        (3, "resolutionAndComponentFlags", 0),
        (3, "latitudeOfSouthernPole", -37500000),
        (3, "longitudeOfSouthernPole", 357500000),
        (3, "angleOfRotation", 0),
    )
    assert_grib_message_contents(temp_file_path, expect_values)

    cube_loaded_from_saved = load_cube(temp_file_path)
    _ = cube_loaded_from_saved.data

    # The re-loaded result will not match the original in every respect:
    #  * cube attributes are discarded
    #  * horizontal coordinates are rounded to an integer representation
    #  * bounds on horizontal coords are lost
    # Thus the following "equivalence tests" are rather piecemeal.
    for test_cube in (cube, cube_loaded_from_saved):
        assert test_cube.standard_name == "air_pressure_at_sea_level"
        assert test_cube.units == "Pa"
        assert test_cube.shape == (928, 744)
        assert test_cube.cell_methods == ()

    assert cube_loaded_from_saved.attributes == {
        "GRIB_PARAM": GRIBCode("GRIB2:d000c003n001")
    }

    co_names = [coord.name() for coord in cube.coords()]
    co_names_reload = [coord.name() for coord in cube_loaded_from_saved.coords()]
    assert sorted(co_names_reload) == sorted(co_names)

    for coord_name in co_names:
        co_orig = cube.coord(coord_name)
        co_load = cube_loaded_from_saved.coord(coord_name)
        assert co_load.shape == co_orig.shape, (
            f'Shape of re-loaded "{coord_name}" coord is {co_load.shape} '
            f"instead of {co_orig.shape}"
        )
        np.testing.assert_allclose(co_load.points, co_orig.points, rtol=1.0e-6)

        # Grib does not store x/y bounds, so all re-loaded coords are unbounded.
        assert co_load.bounds is None

    np.testing.assert_allclose(cube.data, cube_loaded_from_saved.data)


@pytest.mark.parametrize(
    ("coord_system_class", "pole"),
    [
        (Stereographic, "north"),
        (Stereographic, "south"),
        (PolarStereographic, "north"),
        (PolarStereographic, "south"),
    ],
)
def test_gdt20_save_load(
    coord_system_class: type[Stereographic],
    pole: Literal["north", "south"],
    tmp_path,
):
    central_lat = 90 if pole == "north" else -90
    coord_system_kwargs = dict(
        central_lat=central_lat,
        central_lon=325,
        true_scale_lat=central_lat,
        ellipsoid=GeogCS(6378169.0),
    )
    coord_system = coord_system_class(**coord_system_kwargs)

    coord_kwargs = dict(units="m", coord_system=coord_system)
    coord_x = DimCoord(
        np.linspace(-2250000, 6750192, 256, endpoint=False),
        standard_name="projection_x_coordinate",
        **coord_kwargs,
    )
    coord_y = DimCoord(
        np.linspace(-980000, -6600000, 160, endpoint=False),
        standard_name="projection_y_coordinate",
        **coord_kwargs,
    )
    coord_t = DimCoord(0, standard_name="time", units="hours since 1970-01-01 00:00:00")
    coord_fp = DimCoord(0, standard_name="forecast_period", units="hours")
    coord_frt = DimCoord(
        0, standard_name="forecast_reference_time", units=coord_t.units
    )

    shape = (coord_y.shape[0], coord_x.shape[0])
    cube = Cube(
        np.arange(np.prod(shape), dtype=float).reshape(shape),
        dim_coords_and_dims=[(coord_y, 0), (coord_x, 1)],
        aux_coords_and_dims=[(coord_t, None), (coord_fp, None), (coord_frt, None)],
    )

    temp_file_path = tmp_path / "polar_stereo.grib2"
    save(cube, temp_file_path)
    cube_reloaded = load_cube(temp_file_path)
    _ = cube_reloaded.data

    cube_expected = cube.copy()
    for coord in cube_expected.dim_coords:
        # GRIB only describes PolarStereographic, so we always expect that
        # system even when we started with Stereographic.
        coord.coord_system = PolarStereographic(**coord_system_kwargs)

    del cube_reloaded.attributes["GRIB_PARAM"]
    for coord in cube_reloaded.dim_coords:
        coord.points = np.round(coord.points)

    assert cube_expected == cube_reloaded


@pytest.fixture(params=[True, False], ids=["recordGDT", "norecordGDT"])
def record(request):
    record = bool(request.param)
    with TEMPLATE_RECORD.context(record=record):
        yield record


def test_gdt40_loadsave(tmp_path, record):
    loadpath = tests.get_data_path(("GRIB", "reduced", "reduced_gg.grib2"))
    cube = load_cube(loadpath)
    print(cube)

    # This kludge is needed for now to make it saveable
    #  - ASIS: fails to add pressure factory on load, so has no vertical coord
    cube.coord("level_pressure").rename("pressure")
    # Removing these *also* allows the "coord_dims_names" check to match.
    cube.remove_coord("model_level_number")
    cube.remove_coord("sigma")

    if record:
        assert cube.attributes["GRIB2_GRID_TEMPLATE"] == 40
    else:
        assert "GRIB2_GRID_TEMPLATE" not in cube.attributes

    savepath = tmp_path / "tmp.grib2"
    if not record:
        msg = (
            "Expected to find exactly 1 coordinate, but found 2. "
            "They were: latitude, longitude."
        )
        with pytest.raises(CoordinateNotFoundError, match=msg):
            save(cube, savepath)
    else:
        save(cube, savepath)
        cube_reloaded = load_cube(savepath)

        def coord_dims_names(cube):
            return [
                [co.name() for co in cube.coords(dimensions=i_dim)]
                for i_dim in list(range(cube.ndim)) + [()]
            ]

        print("\nORIGINAL:")
        print(cube)
        print(coord_dims_names(cube))
        print("\n\nRELOADED:")
        print(cube_reloaded)
        print(coord_dims_names(cube_reloaded))
        assert coord_dims_names(cube_reloaded) == coord_dims_names(cube)
        assert np.all(cube_reloaded.data == cube.data)
