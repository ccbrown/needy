import json
import os
import sys

from .functional_test import TestCase


class InitTest(TestCase):
    def test_init(self):
        empty_directory = os.path.join(self.path(), 'empty')
        os.makedirs(empty_directory)
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'project': {
                        'directory': empty_directory,
                        'project': {
                            'build-steps': 'echo foo > bar'
                        }
                    }
                }
            }))
        self.assertEqual(self.execute(['satisfy', 'project']), 0)
        self.assertTrue(os.path.exists(os.path.join(self.source_directory('project'), 'bar')))
        self.assertEqual(self.execute(['init', 'project']), 0)
        self.assertFalse(os.path.exists(os.path.join(self.source_directory('project'), 'bar')))
