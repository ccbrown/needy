import json
import os

from ..functional_test import TestCase


class CustomProjectTest(TestCase):
    def test_basics(self):
        empty_directory = os.path.join(self.path(), 'empty')
        os.makedirs(empty_directory)
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'project': {
                        'directory': empty_directory,
                        'project': {
                            'configure-steps': [
                                'export FOO=QWERTYUIOP',
                                'echo $FOO > foo'
                            ],
                            'build-steps': [
                                'cat foo | grep "QWERTYUIOP"'
                            ]
                        }
                    }
                }
            }))
        self.assertEqual(self.execute(['satisfy', 'project']), 0)
