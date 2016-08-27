import os
import sys
import textwrap

from .functional_test import TestCase


class NeedyTest(TestCase):
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
                            build-steps: echo {{{{ build_directory('mylib') }}}} | {match_command} "suffix"
            ''').format(
                empty_directory=empty_directory,
                match_command='findstr' if sys.platform == 'win32' else 'grep'
            ))
        self.assertEqual(self.execute(['satisfy']), 0)
