"""
Perform test automation with nox.

For further details, see https://nox.thea.codes/en/stable/#

"""

from asyncore import write
from csv import excel
import hashlib
import os
from pathlib import Path

import nox


#: Default to reusing any pre-existing nox environments.
nox.options.reuse_existing_virtualenvs = True

#: Name of the package to test.
PACKAGE = str("iris_grib")

#: Cirrus-CI environment variable hook.
PY_VER = os.environ.get("PY_VER", ["3.6", "3.7", "3.8"])

#: Default cartopy cache directory.
CARTOPY_CACHE_DIR = os.environ.get("HOME") / Path(".local/share/cartopy")


def venv_cached(session):
    """
    Determine whether the nox session environment has been cached.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    Returns
    -------
    bool
        Whether the session has been cached.

    """
    result = False
    yml = Path(f"requirements/ci/py{session.python.replace('.', '')}.yml")
    tmp_dir = Path(session.create_tmp())
    cache = tmp_dir / yml.name
    if cache.is_file():
        with open(yml, "rb") as fi:
            expected = hashlib.sha256(fi.read()).hexdigest()
        with open(cache, "r") as fi:
            actual = fi.read()
        result = actual == expected
    return result


def cache_venv(session):
    """
    Cache the nox session environment.

    This consists of saving a hexdigest (sha256) of the associated
    conda requirements YAML file.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    yml = Path(f"requirements/ci/py{session.python.replace('.', '')}.yml")
    with open(yml, "rb") as fi:
        hexdigest = hashlib.sha256(fi.read()).hexdigest()
    tmp_dir = Path(session.create_tmp())
    cache = tmp_dir / yml.name
    with open(cache, "w") as fo:
        fo.write(hexdigest)


def cache_cartopy(session):
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

def write_iris_config(session):
    """Add test data dir and libudunits2.so to iris config"""
    try:
        test_data_dir = session.posargs[session.posargs.index('--test-data-dir')+1]
    except:
        test_data_dir = ""
    iris_config_file = os.path.join(session.virtualenv.location, 'lib', f'python{session.python}', 'site-packages', 'iris', 'etc', 'site.cfg')
    iris_config = f"""
[Resources]
test_data_dir = {test_data_dir}
[System]
udunits2_path = {os.path.join(session.virtualenv.location, 'lib', 'libudunits2.so')}
"""

    print("Iris config\n-----------")
    print(iris_config)

    with open(iris_config_file, 'w') as f:
        f.write(iris_config)

def prepare_venv(session):
    """
    Create and cache the nox session conda environment, and additionally
    provide conda environment package details and info.

    Note that, iris-grib is installed into the environment using pip.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    Notes
    -----
    See
      - https://github.com/theacodes/nox/issues/346
      - https://github.com/theacodes/nox/issues/260

    """
    if not venv_cached(session):
        # Determine the conda requirements yaml file.
        fname = f"requirements/ci/py{session.python.replace('.', '')}.yml"
        # Back-door approach to force nox to use "conda env update".
        command = (
            "conda",
            "env",
            "update",
            f"--prefix={session.virtualenv.location}",
            f"--file={fname}",
            "--prune",
        )
        session._run(*command, silent=True, external="error")
        write_iris_config(session)
        cache_venv(session)

    cache_cartopy(session)
    session.install("--no-deps", "--editable", ".")

    # Determine whether verbose diagnostics have been requested
    # from the command line.
    verbose = "-v" in session.posargs or "--verbose" in session.posargs

    if verbose:
        session.run("conda", "info")
        session.run("conda", "list", f"--prefix={session.virtualenv.location}")
        session.run(
            "conda",
            "list",
            f"--prefix={session.virtualenv.location}",
            "--explicit",
        )


@nox.session
def flake8(session):
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
def black(session):
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
def tests(session):
    """
    Perform iris-grib system, integration and unit tests.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    prepare_venv(session)
    session.run(
        "python",
        "-m",
        "iris_grib.tests.runner",
        "--default-tests",
        "--unit-tests",
        "--integration-tests",
    )


@nox.session(python=PY_VER, venv_backend="conda")
def eccodes(session):
    """Perform 'selfcheck' test of eccodes.
    
        Parameters
        ----------
        session: object
            A `nox.sessions.Session` object.
    """
    prepare_venv(session)
    session.run("python", "-m", "eccodes", "selfcheck")


@nox.session(python=PY_VER, venv_backend="conda")
def doctest(session):
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
def linkcheck(session):
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
