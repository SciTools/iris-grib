# (C) British Crown Copyright 2014 - 2019, Met Office
#
# This file is part of iris-grib.
#
# iris-grib is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-grib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-grib.  If not, see <http://www.gnu.org/licenses/>.
"""
Tests for function :func:`iris_grib._load_convert.product_definition_section`.

"""

# QUESTIONS
# tests here will overlap with individual template tests, as they are all
#   called within product_definition_section. Is this a problem?
# a lot of tests have unused imports, seemingly because they were copied from
#   other tests. Is this standard practice?

from __future__ import (absolute_import, division, print_function)
from six.moves import (filter, input, map, range, zip)  # noqa

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from copy import deepcopy
import mock

from cf_units import Unit
from iris.coords import DimCoord

from iris_grib._load_convert import product_definition_section
from iris_grib.grib_phenom_translation import _GribToCfDataClass

from iris_grib.tests.unit.load_convert import empty_metadata
from iris_grib.tests.unit.load_convert.test_product_definition_template_0 \
    import section_4 as template_0

class Test(tests.IrisGribTest):
    def test_fixed_surface_present(self):
        rt_coord = mock.sentinel.observation_time
        metadata = empty_metadata()
        section_4 = template_0()
        product_definition_section(section_4, metadata, rt_coord)



    # def test_fixed_surface_absent:

