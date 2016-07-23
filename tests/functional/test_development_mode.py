import json
import os
import platform

from .functional_test import TestCase


class DevelopmentModeTest(TestCase):
    def test_basics(self):
        source_directory = os.path.join(self.path(), 'source')
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
                        'host': [platform.machine()]
                    }
                }
            }))

        # start with a normal build
        with open(os.path.join(source_directory, 'test'), 'w') as test:
            test.write('a')
        self.assertEqual(self.execute(['satisfy', 'mylib', '-u', 'test']), 0)
        output_test_file = os.path.join(self.build_directory('mylib', 'test'), 'test')
        with open(output_test_file, 'r') as test:
            self.assertEqual(test.read(), 'a')

        # modifying the source directory should have no effect - we already have an up-to-date build
        with open(os.path.join(source_directory, 'test'), 'w') as test:
            test.write('b')
        self.assertEqual(self.execute(['satisfy', 'mylib', '-u', 'test']), 0)
        output_test_file = os.path.join(self.build_directory('mylib', 'test'), 'test')
        with open(output_test_file, 'r') as test:
            self.assertEqual(test.read(), 'a')

        # go into dev mode
        self.assertNotEqual(self.execute(['dev-mode', 'mylib', '--query']), 0)
        self.assertEqual(self.execute(['dev-mode', 'mylib']), 0)
        self.assertEqual(self.execute(['dev-mode', 'mylib', '--query']), 0)

        # now modifications should take effect - in dev mode, we should always be considered out-dated
        with open(os.path.join(source_directory, 'test'), 'w') as test:
            test.write('c')
        self.assertEqual(self.execute(['satisfy', 'mylib', '-u', 'test']), 0)
        output_test_file = os.path.join(self.build_directory('mylib', 'test'), 'test')
        with open(output_test_file, 'r') as test:
            self.assertEqual(test.read(), 'c')

        # disable dev mode
        self.assertEqual(self.execute(['dev-mode', 'mylib', '--disable']), 0)
        self.assertNotEqual(self.execute(['dev-mode', 'mylib', '--query']), 0)
