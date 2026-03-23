Phenomenon translation
======================

``iris-grib`` attempts to translate between CF phenomenon identities
(i.e. 'standard_name' and possibly 'long_name' attributes), and GRIB parameter codes,
when converting cubes to or from the GRIB format.

A set of tables define known CF translations for GRIB1 and GRIB2 parameters, and can be
interrogated with the functions in :mod:`iris_grib.grib_phenom_translation`.

Parameter loading record
------------------------
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
------------------------
When a cube has a ``GRIB_PARAM`` attribute, as described above, this controls what the
relevant message keys are set to on saving.
(N.B. at present applies only to GRIB2, since we don't support GRIB1 saving)
