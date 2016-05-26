import json
import os

from .functional_test import TestCase


class XCConfigTest(TestCase):
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
        self.assertEqual(self.execute(['generate', 'xcconfig']), 0)
        # this is about the best we can do for a generic functional test - the file will be empty on anything but osx
        self.assertTrue(os.path.isfile(os.path.join(self.needs_directory(), 'search-paths.xcconfig')))
