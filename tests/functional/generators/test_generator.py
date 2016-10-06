import yaml
import os
import sys
import textwrap

from ..functional_test import TestCase


class GeneratorTest(TestCase):
    def test_needy_variables(self):
        empty_directory = os.path.join(self.path(), 'empty')
        os.makedirs(empty_directory)
        default_suffix = 'default-suffix'
        with open(os.path.join(self.path(), 'needs.yaml'), 'w') as needs_file:
            needs_file.write(textwrap.dedent('''
                libraries:
                    mylib:
                        directory: {empty_directory}
                        build-directory-suffix: {{{{ suffix|default(\'{default_suffix}\') }}}}
                        project:
                            build-steps:
                                - echo noop
            ''').format(
                empty_directory=empty_directory,
                default_suffix=default_suffix,
            ))

        def assert_with_suffix(suffix):
            self.assertEqual(self.execute(['generate', 'jamfile', '-Dsuffix={}'.format(suffix)]), 0)
            generated_file = os.path.join(self.needs_directory(), 'Jamfile')
            with open(generated_file, 'r') as f:
                contents = f.read()
            print(contents)
            self.assertTrue(suffix in contents)
            self.assertFalse('foobar' in contents)

        assert_with_suffix('suffix-foo')
        assert_with_suffix('suffix-bar')
