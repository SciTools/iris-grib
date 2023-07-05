# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Perform test automation with nox.

For further details, see https://nox.thea.codes/en/stable/#

"""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path

import nox
from nox.logger import logger

#: Default to reusing any pre-existing nox environments.
nox.options.reuse_existing_virtualenvs = True

#: Name of the package to test.
PACKAGE = str("iris_grib")

#: Cirrus-CI environment variable hook.
PY_VER = os.environ.get("PY_VER", ["3.9", "3.10", "3.11"])
IRIS_SOURCE = os.environ.get("IRIS_SOURCE", ['source', 'conda-forge'])

#: Default cartopy cache directory.
CARTOPY_CACHE_DIR = os.environ.get("HOME") / Path(".local/share/cartopy")


def _cache_cartopy(session: nox.sessions.Session) -> None:
    """
    Determine whether to cache the cartopy natural earth shapefiles.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    if not CARTOPY_CACHE_DIR.is_dir():
        session.run(
            "python",
            "-c",
            "import cartopy; cartopy.io.shapereader.natural_earth()",
        )


def _write_iris_config(session: nox.sessions.Session) -> None:
    """
    Add test data dir and libudunits2.so to iris config.

    test data dir is set from session pos args. i.e. can be
    configured by passing in on the command line:
        nox --session tests -- --test-data-dir $TEST_DATA_DIR/test_data

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    try:
        test_data_dir = session.posargs[
            session.posargs.index('--test-data-dir')+1
            ]
    except Exception:
        test_data_dir = ""

    iris_config_file = os.path.join(
        session.virtualenv.location,
        'lib',
        f'python{session.python}',
        'site-packages',
        'iris',
        'etc',
        'site.cfg',
    )
    iris_config = f"""
[Resources]
test_data_dir = {test_data_dir}
[System]
udunits2_path = {
    os.path.join(session.virtualenv.location,'lib', 'libudunits2.so')
}
"""

    print("Iris config\n-----------")
    print(iris_config)

    with open(iris_config_file, 'w') as f:
        f.write(iris_config)


def _session_lockfile(session: nox.sessions.Session) -> Path:
    """
    Return the path of the session lockfile for the relevant python string
    e.g ``py38``.

    """
    lockfile_name = f"py{session.python.replace('.', '')}-linux-64.lock"
    return Path("requirements/locks") / lockfile_name


def _file_content(file_path: Path) -> str:
    with file_path.open("r") as file:
        return file.read()


def _session_cachefile(session: nox.sessions.Session) -> Path:
    """Return the path of the session lockfile cache."""
    tmp_dir = Path(session.create_tmp())
    cache = tmp_dir / _session_lockfile(session).name
    return cache


def _venv_populated(session: nox.sessions.Session) -> bool:
    """
    Return True if the Conda venv has been created and the list of packages in
    the lockfile installed.

    """
    return _session_cachefile(session).is_file()


def _venv_changed(session: nox.sessions.Session) -> bool:
    """
    Return True if the installed session is different to that specified in the
    lockfile.

    """
    result = False
    if _venv_populated(session):
        expected = _file_content(_session_lockfile(session))
        actual = _file_content(_session_cachefile(session))
        result = actual != expected
    return result


def _install_and_cache_venv(session: nox.sessions.Session) -> None:
    """
    Install and cache the nox session environment.
    This consists of saving a hexdigest (sha256) of the associated
    Conda lock file.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    lockfile = _session_lockfile(session)
    session.conda_install(f"--file={lockfile}")

    with open(lockfile, "rb") as fi:
        hexdigest = hashlib.sha256(fi.read()).hexdigest()
    with _session_cachefile(session).open("w") as cachefile:
        cachefile.write(hexdigest)


@contextmanager
def prepare_venv(
    session: nox.sessions.Session, iris_source: str = 'conda_forge'
) -> None:
    """
    Create and cache the nox session conda environment, and additionally
    provide conda environment package details and info.

    Note that, iris-grib is installed into the environment using pip.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    iris_source: str
        Determines where Iris was sourced from. Either 'conda_forge' (the
        default), or 'source' which refers to the Iris main branch.

    Notes
    -----
    See
      - https://github.com/theacodes/nox/issues/346
      - https://github.com/theacodes/nox/issues/260

    """
    venv_dir = session.virtualenv.location_name

    if not _venv_populated(session):
        # Environment has been created but packages not yet installed.
        # Populate the environment from the lockfile.
        logger.debug(f"Populating conda env: {venv_dir}")
        _install_and_cache_venv(session)

    elif _venv_changed(session):
        # Destroy the environment and rebuild it.
        logger.debug(f"Lockfile changed. Recreating conda env: {venv_dir}")
        _reuse_original = session.virtualenv.reuse_existing
        session.virtualenv.reuse_existing = False
        session.virtualenv.create()
        _install_and_cache_venv(session)
        session.virtualenv.reuse_existing = _reuse_original

    logger.debug(f"Environment up to date: {venv_dir}")

    if iris_source == 'source':
        # get latest iris
        iris_dir = f"{session.create_tmp()}/iris"

        if os.path.exists(iris_dir):
            # cached.  update by pulling from origin/master
            session.run(
                "git",
                "-C",
                iris_dir,
                "pull",
                "origin",
                "main",
                external=True  # use git from host environment
            )
        else:
            session.run(
                "git",
                "clone",
                "https://github.com/scitools/iris.git",
                iris_dir,
                external=True
            )
        session.install(iris_dir, '--no-deps')

    _cache_cartopy(session)
    _write_iris_config(session)

    # Install the iris-grib source in develop mode.
    session.install("--no-deps", "--editable", ".")

    # Determine whether verbose diagnostics have been requested
    # from the command line.
    verbose = "-v" in session.posargs or "--verbose" in session.posargs

    if verbose:
        session.run("conda", "info")
        session.run("conda", "list", f"--prefix={venv_dir}")
        session.run(
            "conda",
            "list",
            f"--prefix={venv_dir}",
            "--explicit",
        )


@nox.session
def flake8(session: nox.sessions.Session):
    """
    Perform flake8 linting of iris-grib.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    # Pip install the session requirements.
    session.install("flake8")
    # Execute the flake8 linter on the package.
    session.run("flake8", PACKAGE)
    # Execute the flake8 linter on this file.
    session.run("flake8", __file__)


@nox.session
def black(session: nox.sessions.Session):
    """
    Perform black format checking of iris-grib.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    # Pip install the session requirements.
    session.install("black==20.8b1")
    # Execute the black format checker on the package.
    session.run("black", "--check", PACKAGE)
    # Execute the black format checker on this file.
    session.run("black", "--check", __file__)


@nox.session(python=PY_VER, venv_backend="conda")
@nox.parametrize('iris_source', IRIS_SOURCE)
def tests(session: nox.sessions.Session, iris_source: str):
    """
    Perform iris-grib tests against release and development versions of iris.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    iris_source: str
        Either 'conda_forge' if using Iris from conda-forge, or 'source' if
        installing Iris from the Iris' main branch.

    """
    prepare_venv(session, iris_source)

    session.run("python", "-m", "eccodes", "selfcheck")

    session.run(
        "python",
        "-m",
        "iris_grib.tests.runner",
        "--default-tests",
    )


@nox.session(python=PY_VER, venv_backend="conda")
def doctest(session: nox.sessions.Session):
    """
    Perform iris-grib doc-tests.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    prepare_venv(session)
    session.cd("docs")
    session.run(
        "make",
        "clean",
        "html",
        external=True,
    )
    session.run(
        "make",
        "doctest",
        external=True,
    )


@nox.session(python=PY_VER, venv_backend="conda")
def linkcheck(session: nox.sessions.Session):
    """
    Perform iris-grib doc link check.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    prepare_venv(session)
    session.cd("docs")
    session.run(
        "make",
        "clean",
        "html",
        external=True,
    )
    session.run(
        "make",
        "linkcheck",
        external=True,
    )
