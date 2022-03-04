# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Tests for function :func:`iris_grib._load_convert.translate_phenomenon`.

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from cf_units import Unit
from iris.coords import DimCoord

from iris_grib._load_convert import Probability, translate_phenomenon
from iris_grib.grib_phenom_translation import _GribToCfDataClass, GRIBCode


class Test_probability(tests.IrisGribTest):
    def setUp(self):
        # Patch inner call to return a given phenomenon type.
        target_module = 'iris_grib._load_convert'
        self.phenom_lookup_patch = self.patch(
            target_module + '.itranslation.grib2_phenom_to_cf_info',
            return_value=_GribToCfDataClass('air_temperature', '', 'K', None))
        # Construct dummy call arguments
        self.probability = Probability('<prob_type>', 22.0)
        self.metadata = {'aux_coords_and_dims': [], 'attributes': {}}

    def test_basic(self):
        translate_phenomenon(self.metadata, 7, 8, 9, None,
                             None, None, probability=self.probability)
        # Check metadata.
        thresh_coord = DimCoord([22.0],
                                standard_name='air_temperature',
                                long_name='', units='K')
        self.assertEqual(self.metadata, {
            'standard_name': None,
            'long_name': 'probability_of_air_temperature_<prob_type>',
            'units': Unit(1),
            'aux_coords_and_dims': [(thresh_coord, None)],
            'attributes': {'GRIB_PARAM': GRIBCode(2, 7, 8, 9)}})

    def test_no_phenomenon(self):
        self.phenom_lookup_patch.return_value = None
        expected_metadata = self.metadata.copy()
        translate_phenomenon(self.metadata,
                             discipline=7,
                             parameterCategory=77,
                             parameterNumber=777,
                             typeOfFirstFixedSurface=None,
                             scaledValueOfFirstFixedSurface=None,
                             typeOfSecondFixedSurface=None,
                             probability=self.probability)
        expected_metadata['attributes']['GRIB_PARAM'] = \
            GRIBCode(2, 7, 77, 777)
        self.assertEqual(self.metadata, expected_metadata)


if __name__ == '__main__':
    tests.main()
