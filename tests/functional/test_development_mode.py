import json
import os
import platform

from .functional_test import TestCase


class DevelopmentModeTest(TestCase):
    def test_basics(self):
        source_directory = os.path.join(self.path(), 'src')
        os.makedirs(source_directory)
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'mylib': {
                        'directory': source_directory,
                        'project': {
                            'build-steps': 'cp ./test {build_directory}/test'
                        }
                    }
                },
                'universal-binaries': {
                    'test': {
                        'host': [platform.machine().lower()]
                    }
                }
            }))
        mylib_source_directory = os.path.join(self.needs_directory(), 'mylib', 'source')

        # start with a normal build
        with open(os.path.join(source_directory, 'test'), 'w') as test:
            test.write('a')
        self.assertEqual(self.execute(['satisfy', 'mylib', '-u', 'test']), 0)
        output_test_file = os.path.join(self.build_directory('mylib', 'test'), 'test')
        with open(output_test_file, 'r') as test:
            self.assertEqual(test.read(), 'a')

        # modifying the source directory should have no effect - we already have an up-to-date build
        with open(os.path.join(mylib_source_directory, 'test'), 'w') as test:
            test.write('b')
        self.assertEqual(self.execute(['satisfy', 'mylib', '-u', 'test']), 0)
        output_test_file = os.path.join(self.build_directory('mylib', 'test'), 'test')
        with open(output_test_file, 'r') as test:
            self.assertEqual(test.read(), 'a')

        # go into dev mode
        self.assertNotEqual(self.execute(['dev', 'status', 'mylib']), 0)
        self.assertEqual(self.execute(['dev', 'enable', 'mylib']), 0)
        self.assertEqual(self.execute(['dev', 'status', 'mylib']), 0)

        # now modifications should take effect - in dev mode, we should always be considered out-dated
        with open(os.path.join(mylib_source_directory, 'test'), 'w') as test:
            test.write('c')
        self.assertEqual(self.execute(['satisfy', 'mylib', '-u', 'test']), 0)
        output_test_file = os.path.join(self.build_directory('mylib', 'test'), 'test')
        with open(output_test_file, 'r') as test:
            self.assertEqual(test.read(), 'c')

        # disable dev mode
        self.assertEqual(self.execute(['dev', 'disable', 'mylib']), 0)
        self.assertNotEqual(self.execute(['dev', 'status', 'mylib']), 0)

    def test_synchronize(self):
        source_directory = os.path.join(self.path(), 'src')
        os.makedirs(source_directory)
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'miniupnpc': {
                        'repository': 'https://github.com/miniupnp/miniupnp.git',
                        'commit': 'f2d54a84aa7c8e6927f7f43987b7eb779bb44603'
                    }
                }
            }))
        miniupnpc_source_directory = os.path.join(self.needs_directory(), 'miniupnpc', 'source')

        self.assertEqual(self.execute(['init', 'miniupnpc']), 0)

        # go into dev mode
        self.assertNotEqual(self.execute(['dev', 'status', 'miniupnpc']), 0)
        self.assertEqual(self.execute(['dev', 'enable', 'miniupnpc']), 0)
        self.assertEqual(self.execute(['dev', 'status', 'miniupnpc']), 0)

        # modify some files in the source tree
        test_file = os.path.join(miniupnpc_source_directory, 'test')
        readme_file = os.path.join(miniupnpc_source_directory, 'README')
        with open(test_file, 'w') as untracked:
            untracked.write('c')
        with open(readme_file, 'w') as tracked:
            tracked.write('d')

        # move to a new commit, uncommitted changes should remain
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'miniupnpc': {
                        'repository': 'https://github.com/miniupnp/miniupnp.git',
                        'commit': '370bf72e7282752e04e54ee9e5f13a80a95082f3'
                    }
                }
            }))
        self.assertEqual(self.execute(['dev', 'sync', 'miniupnpc']), 0)

        # verify that the test file still exists in the source tree
        with open(test_file, 'r') as untracked:
            self.assertEqual(untracked.read(), 'c')
        with open(readme_file, 'r') as tracked:
            self.assertEqual(tracked.read(), 'd')

        # disable dev mode
        self.assertEqual(self.execute(['dev', 'disable', 'miniupnpc']), 0)

        # sync should now fail
        self.assertRaises(RuntimeError, lambda: self.execute(['dev', 'sync', 'miniupnpc']))
        self.assertEqual(self.execute(['dev', 'sync']), 0)
