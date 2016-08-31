import json
import os
import sys

from ..functional_test import TestCase


class PkgConfigJamTest(TestCase):
    if sys.platform != 'win32':
        def test_generate(self):
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

            os.environ['PKG_CONFIG_PATH'] = self.pkg_config_path()
            self.assertEqual(self.execute(['generate', 'pkgconfig-jam']), 0)

            path = os.path.join(self.needs_directory(), 'pkgconfig.jam')
            self.assertTrue(os.path.isfile(path))
            with open(path, 'r') as f:
                contents = f.read()
            self.assertTrue('cereal' in contents)
