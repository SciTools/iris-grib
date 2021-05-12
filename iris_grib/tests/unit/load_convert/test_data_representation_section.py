# Copyright iris-grib contributors
#
# This file is part of iris-grib and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test function :func:`iris_grib._load_convert.data_representation_section.`

"""

# import iris_grib.tests first so that some things can be initialised
# before importing anything else.
import iris_grib.tests as tests

from iris.exceptions import TranslationError

from iris_grib._load_convert import data_representation_section
from iris_grib.tests.unit import _make_test_message


class Test(tests.IrisGribTest):
    def test_supported_templates(self):
        template_nums = [0, 1, 2, 3, 4, 40, 41, 42, 50, 51, 61]
        for template_num in template_nums:
            message = _make_test_message(
                {5: {'dataRepresentationTemplateNumber': template_num}})
            data_representation_section(message.sections[5])

    def test_unsupported_template(self):
        message = _make_test_message(
            {5: {'dataRepresentationTemplateNumber': 5}})
        err_msg = r'Template \[5\] is not supported'
        with self.assertRaisesRegex(TranslationError, err_msg):
            data_representation_section(message.sections[5])


if __name__ == '__main__':
    tests.main()
