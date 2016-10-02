import distutils.spawn
import json
import os
import sys
import textwrap

from .functional_test import TestCase

from needy.override_environment import OverrideEnvironment
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

    def test_clean(self):
        empty_directory = os.path.join(self.path(), 'empty')
        os.makedirs(empty_directory)
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'project': {
                        'directory': empty_directory,
                        'project': {
                            'build-steps': [
                                'cd {{ build_directory(\'project\')|json_escape }}',
                                'echo foo > bar'
                            ]
                        }
                    },
                    'project2': {
                        'directory': empty_directory,
                        'project': {
                            'build-steps': [
                                'echo foo > bar',
                                'cd {{ build_directory(\'project2\')|json_escape }}',
                                'echo foo > bar'
                            ]
                        }
                    }
                }
            }))
        self.assertEqual(self.execute(['satisfy', 'project']), 0)
        self.assertTrue(os.path.exists(os.path.join(self.build_directory('project'), 'bar')))

        # fails in dev mode
        self.assertEqual(self.execute(['dev', 'enable', 'project']), 0)
        self.assertRaises(RuntimeError, lambda: self.execute(['clean', 'project']))
        self.assertTrue(os.path.exists(os.path.join(self.build_directory('project'), 'bar')))

        # doesn't fail if a filter covers more than one library
        self.assertEqual(self.execute(['dev', 'enable', 'project']), 0)
        self.assertEqual(self.execute(['clean']), 0)
        self.assertTrue(os.path.exists(os.path.join(self.build_directory('project'), 'bar')))

        self.assertEqual(self.execute(['satisfy', 'project']), 0)
        self.assertTrue(os.path.exists(os.path.join(self.build_directory('project'), 'bar')))

        self.assertEqual(self.execute(['dev', 'disable', 'project']), 0)
        self.assertEqual(self.execute(['clean', 'project']), 0)
        self.assertFalse(os.path.exists(os.path.join(self.build_directory('project'), 'bar')))

        # clean only the build directory
        self.assertEqual(self.execute(['satisfy', 'project2']), 0)
        self.assertTrue(os.path.exists(os.path.join(self.source_directory('project2'), 'bar')))
        self.assertTrue(os.path.exists(os.path.join(self.build_directory('project2'), 'bar')))
        self.assertEqual(self.execute(['clean', 'project2', '--build-directory']), 0)
        self.assertFalse(os.path.exists(os.path.join(self.build_directory('project2'), 'bar')))
        self.assertTrue(os.path.exists(os.path.join(self.source_directory('project2'), 'bar')))

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

        # same thing with dev mode
        self.assertEqual(self.execute(['dev', 'enable', 'project']), 0)
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

    if distutils.spawn.find_executable('pkg-config'):
        def test_pkgconfig_dependency_injection(self):
            empty_directory = os.path.join(self.path(), 'empty')
            os.makedirs(empty_directory)
            with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
                needs_file.write(json.dumps({
                    'libraries': {
                        'a': {
                            'directory': empty_directory,
                            'dependencies': 'b',
                            'project': {
                                'build-steps': 'echo foo > {build_directory}/bar'
                            }
                        },
                        'b': {
                            'directory': empty_directory,
                            'dependencies': 'c',
                            'project': {
                                'build-steps': 'echo foo > {build_directory}/bar'
                            }
                        },
                        'c': {
                            'directory': empty_directory,
                            'project': {
                                'build-steps': 'echo foo > {build_directory}/bar'
                            }
                        }
                    }
                }))
            pkgconfig_directory = os.path.join(self.path(), 'pkgconfig')
            os.makedirs(pkgconfig_directory)
            with open(os.path.join(pkgconfig_directory, 'b.pc'), 'w') as pkgconfig_file:
                pkgconfig_file.write(textwrap.dedent('''
                    prefix=${pcfiledir}/../..
                    exec_prefix=${prefix}
                    libdir=${exec_prefix}/lib
                    includedir=${prefix}/include

                    Name: b
                    Version: 0
                    Description: b
                    Libs: -L${libdir}
                    Cflags: -I${includedir}
                '''))
            with OverrideEnvironment({'PKG_CONFIG_PATH': pkgconfig_directory}):
                self.assertEqual(self.execute(['satisfy', 'a']), 0)
                self.assertTrue(os.path.exists(os.path.join(self.build_directory('a'), 'bar')))
                self.assertFalse(os.path.exists(os.path.join(self.build_directory('b'), 'bar')))
                self.assertFalse(os.path.exists(os.path.join(self.build_directory('c'), 'bar')))
