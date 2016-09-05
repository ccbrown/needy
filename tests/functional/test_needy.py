import json
import os
import sys
import textwrap

from .functional_test import TestCase

from needy.platforms import host_platform


class NeedyTest(TestCase):
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

    def test_status(self):
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
                },
                'universal-binaries': {
                    'ub': {
                        'host': [host_platform()().default_architecture()]
                    }
                }
            }))
        self.assertEqual(self.execute(['status']), 0)
        self.assertEqual(self.execute(['status', '-u', 'ub']), 0)
        self.assertEqual(self.execute(['satisfy', 'project']), 0)
        self.assertEqual(self.execute(['status']), 0)
        self.assertEqual(self.execute(['status', '-u', 'ub']), 0)

    def test_yaml_jinja(self):
        empty_directory = os.path.join(self.path(), 'empty')
        os.makedirs(empty_directory)
        with open(os.path.join(self.path(), 'needs.yaml'), 'w') as needs_file:
            needs_file.write(textwrap.dedent('''
                libraries:
                    mylib:
                        directory: {empty_directory}
                        build-directory-suffix: suffix
                        project:
                            build-steps:
                                - echo {{{{ build_directory('mylib') }}}} | {match_command} "suffix"
                                - echo {{{{ architecture }}}} | {match_command} "{architecture}"
                universal-binaries:
                    ub:
                        host: ['{architecture}']
            ''').format(
                empty_directory=empty_directory,
                match_command='findstr' if sys.platform == 'win32' else 'grep',
                architecture=host_platform()().default_architecture()
            ))
        self.assertEqual(self.execute(['satisfy', '-u', 'ub']), 0)
