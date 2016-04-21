import json
import os
import shutil
import tempfile
import unittest

import needy.needy


class NeedyTestDirectory:

    def __init__(self, yaml):
        self.__yaml = yaml

    def __enter__(self):
        self.__path = tempfile.mkdtemp()
        with open(os.path.join(self.__path, 'needs.json'), 'w') as f:
            f.write(self.__yaml)
        return self

    def __exit__(self, etype, value, traceback):
        shutil.rmtree(self.__path)

    def path(self):
        return self.__path


class NeedyTest(unittest.TestCase):

    def test_libraries_to_build(self):
        needs_file = json.dumps({
            'libraries': {
                'excluded': {},
                'dependant': {
                    'dependencies': 'dependency'
                },
                'dependency': {}
            }
        })
        with NeedyTestDirectory(needs_file) as directory:
            n = needy.needy.Needy(directory.path())
            libraries = n.libraries_to_build(n.target('host'), ['dependant'])
            self.assertEqual(len(libraries), 2)
            self.assertEqual(libraries[0][0], 'dependency')
            self.assertEqual(libraries[1][0], 'dependant')
