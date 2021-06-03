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
import yaml

#: Default to reusing any pre-existing nox environments.
nox.options.reuse_existing_virtualenvs = True

#: Name of the package to test. 
PACKAGE = str("iris_grib")

#: Cirrus-CI environment variable hook.
PY_VER = os.environ.get("PY_VER", ["3.7", "3.8"])
IRIS_SOURCE = os.environ.get("IRIS_SOURCE", ['source', 'conda-forge'])

#: Default cartopy cache directory.
CARTOPY_CACHE_DIR = os.environ.get("HOME") / Path(".local/share/cartopy")


def venv_cached(session, requirements_file=None):
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
    if not requirements_file is None:
        yml = Path(requirements_file)
    else:
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


def concat_requirements(primary, *others):
    """Join together the dependencies of one or more requirements.yaml.

    Parameters
    ----------
    primary: str
        filename of the primary requirements.yaml

    others: list[str]
        list of additional requirements.yamls
    
    Returns
    -------
    yaml
        Dictionary of yaml data: primary with the addition
        of others[]['dependencies']

    """
    with open(primary, 'r') as f:
        requirements = yaml.load(f, yaml.FullLoader)

    for o in others:
        with open(o, 'r') as f:
            oreq = yaml.load(f, yaml.FullLoader)
            requirements['dependencies'].extend(oreq['dependencies'])
    
    return requirements


def cache_venv(session, requirements_file=None):
    """
    Cache the nox session environment.

    This consists of saving a hexdigest (sha256) of the associated
    conda requirements YAML file.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    if requirements_file is None:
        yml = Path(f"requirements/ci/py{session.python.replace('.', '')}.yml")
    else:
        yml = Path(requirements_file)
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
    """Add test data dir and libudunits2.so to iris config.

    test data dir is set from session pos args. i.e. can be 
    configured by passing in on the command line:
        nox --session tests -- --test-data-dir $TEST_DATA_DIR/test_data
    
    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
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

@contextmanager
def prepare_venv(session, requirements_file=None):
    """
    Create and cache the nox session conda environment, and additionally
    provide conda environment package details and info.

    Note that, iris-grib is installed into the environment using pip.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.
    
    requirements_file: str
        Path to the environment requirements file.
        Default: requirements/ci/py{PY_VER}.yml

    Notes
    -----
    See
      - https://github.com/theacodes/nox/issues/346
      - https://github.com/theacodes/nox/issues/260

    """
    if requirements_file is None:
        # Determine the conda requirements yaml file.
        requirements_file = f"requirements/ci/py{session.python.replace('.', '')}.yml"

    if not venv_cached(session, requirements_file):
        # Back-door approach to force nox to use "conda env update".
        command = (
            "conda",
            "env",
            "update",
            f"--prefix={session.virtualenv.location}",
            f"--file={requirements_file}",
            "--prune",
        )
        session._run(*command, silent=True, external="error")    
        cache_venv(session)

    cache_cartopy(session)

    # Allow the user to do setup things
    # like installing iris-grib in development mode
    yield session
    
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
@nox.parametrize('iris', IRIS_SOURCE)
def tests(session, iris):
    """
    Perform iris-grib tests against release and development versions of iris.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    
    if iris == 'source':
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
                "master",
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
        
        # combine iris and iris-grib requirements into one requirement list
        requirements = concat_requirements(
            f"requirements/ci/py{session.python.replace('.', '')}.yml",
            f"{iris_dir}/requirements/ci/py{session.python.replace('.', '')}.yml"
        )
        # remove iris dependencies, we'll install these from source
        requirements['dependencies'] = [x for x in requirements['dependencies'] 
                                            if not x.startswith('iris')]
        req_file = f"{session.create_tmp()}/requirements.yaml"
        with open(req_file, 'w') as f:
            yaml.dump(requirements, f)
    else:
        req_file = f"requirements/ci/py{session.python.replace('.', '')}.yml"
    
    with prepare_venv(session, req_file):
        if iris == 'source':
            session.install(iris_dir, '--no-deps')
        session.install("--no-deps", "--editable", ".")
        write_iris_config(session)

    session.run("python", "-m", "eccodes", "selfcheck")

    session.run(
        "python",
        "-m",
        "iris_grib.tests.runner",
        "--default-tests",
        "--unit-tests",
        "--integration-tests",
    )



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
