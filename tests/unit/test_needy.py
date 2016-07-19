import json
import os
from pyfakefs import fake_filesystem_unittest

from needy.needy import Needy
from needy.needy_configuration import NeedyConfiguration


class NeedyTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_find_needs_file_with_json_only(self):
        self.fs.CreateFile('needs.json')
        self.assertEqual(Needy.find_needs_file('.'), os.path.sep + 'needs.json')

    def test_find_needs_file_with_yaml_only(self):
        self.fs.CreateFile('needs.yaml')
        self.assertEqual(Needy.find_needs_file('.'), os.path.sep + 'needs.yaml')

    def test_find_needs_file_with_multiple(self):
        self.fs.CreateFile('needs.json')
        self.fs.CreateFile('needs.yaml')
        with self.assertRaises(RuntimeError):
            Needy.find_needs_file('.')

    def test_libraries_to_build(self):
        self.fs.CreateFile('needs.json', contents=json.dumps({
            'libraries': {
                'excluded': {},
                'dependant': {
                    'dependencies': 'dependency'
                },
                'dependency': {}
            }
        }))
        needy = Needy(needy_configuration=NeedyConfiguration(None))
        libraries = needy.libraries_to_build(needy.target('host'), ['dependant'])
        self.assertEqual(len(libraries), 2)
        self.assertEqual(libraries[0][0], 'dependency')
        self.assertEqual(libraries[1][0], 'dependant')
