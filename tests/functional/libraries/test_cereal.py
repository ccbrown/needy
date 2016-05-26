import json
import os

from ..functional_test import TestCase


class CerealTest(TestCase):
    def test_satisfy(self):
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'cereal': {
                        'download': 'https://github.com/USCiLab/cereal/archive/v1.1.2.tar.gz',
                        'checksum': 'fd65224cf628119fe1d85cbca63214c4f6a82e75',
                        'project': {
                            'header-directory': 'include'
                        }
                    }
                }
            }))
        self.assertEqual(self.satisfy(), 0)
        self.assertTrue(os.path.isfile(os.path.join(self.build_directory('cereal'), 'include', 'cereal', 'cereal.hpp')))
        self.assertTrue(os.path.isfile(os.path.join(self.build_directory('cereal'), 'include', 'cereal', 'details', 'util.hpp')))
