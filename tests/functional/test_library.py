import json
import os
import sys

from .functional_test import TestCase


class LibraryTest(TestCase):
    def test_build_environment(self):
        empty_directory = os.path.join(self.path(), 'empty')
        os.makedirs(empty_directory)
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'dependency': {
                        'directory': empty_directory,
                        'project': {
                            'build-steps': []
                        }
                    },
                    'dependent': {
                        'directory': empty_directory,
                        'dependencies': 'dependency',
                        'project': {
                            'build-steps': 'echo %PKG_CONFIG_PATH% | findstr "dependency"'
                        } if sys.platform == 'win32' else {
                            'build-steps': 'echo $PKG_CONFIG_PATH | grep "dependency"'
                        }
                    }
                }
            }))
        self.assertEqual(self.execute(['satisfy', 'dependent']), 0)

    def test_build_directory_suffix(self):
        empty_directory = os.path.join(self.path(), 'empty')
        os.makedirs(empty_directory)
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'mylib': {
                        'directory': empty_directory,
                        'build_directory_suffix': 'foo',
                        'project': {
                            'build-steps': []
                        }
                    }
                }
            }))
        self.assertEqual(self.execute(['satisfy', 'mylib']), 0)
        self.assertEqual(os.path.basename(self.build_directory('mylib')), 'foo')
