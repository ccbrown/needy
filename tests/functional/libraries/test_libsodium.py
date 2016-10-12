import json
import os
import sys

from ..functional_test import TestCase


class LibSodiumTest(TestCase):
    if sys.platform == 'win32':
        def test_satisfy_with_msbuild(self):
            with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
                needs_file.write(json.dumps({
                    'libraries': {
                        'sodium': {
                            'download': 'https://github.com/jedisct1/libsodium/releases/download/1.0.11/libsodium-1.0.11.tar.gz',
                            'checksum': '60f3f3a3f4aea38a103d25844a9e181c0f7b4505',
                            'project': {
                                'header-directory': 'src/libsodium/include'
                            }
                        }
                    }
                }))
            self.assertEqual(self.satisfy(), 0)
            self.assertTrue(os.path.isfile(os.path.join(self.build_directory('lua'), 'include', 'sodium.h')))
            self.assertTrue(os.path.isfile(os.path.join(self.build_directory('lua'), 'lib', 'libsodium.lib')))
