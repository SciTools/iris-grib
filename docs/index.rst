.. iris-grib documentation master file, created by
   sphinx-quickstart on Fri May 13 11:48:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root ``toctree`` directive.

Iris-grib v0.21
===============

The library ``iris-grib`` provides functionality for converting between weather and
climate datasets that are stored as GRIB files and Iris :class:`~iris.cube.Cube`\s.
GRIB files can be loaded as Iris cubes using ``iris-grib`` so that you can use Iris
for analysing and visualising the contents of the GRIB files. Iris cubes can also be
saved to GRIB edition-2 files using ``iris-grib``.


New here?
---------

We recommend:

- :doc:`/how_to/get_started`
- :doc:`/how_to/simple_grib_io`


Navigating this site
--------------------

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * -
     - Description
     - supports ...
     - via ...
   * - Tutorials
     - Guided lessons for understanding a topic.
     - study
     - action
   * - Explanation
     - In-depth discussion for understanding concepts.
     - study
     - theory
   * - How-To Guides
     - Step by step instructions for achieving a specific goal.
     - work
     - action
   * - Reference
     - Concise information to look up when needed.
     - work
     - theory

Read more: `Diataxis.fr`_


.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   tutorial/load_save_api

.. toctree::
   :maxdepth: 1
   :caption: Explanation

   explanation/phenom_translation

.. toctree::
   :maxdepth: 1
   :caption: How-To Guides

   how_to/get_started
   how_to/simple_grib_io
   how_to/modify_during_load

.. toctree::
   :maxdepth: 1
   :caption: Reference

   reference/release_notes
   Iris-grib API </api/modules>


See also
--------

* :ref:`genindex`
* :ref:`modindex`


.. _Diataxis.fr: https://diataxis.fr/
