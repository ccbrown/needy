import json
import os

from ..functional_test import TestCase


class LuaTest(TestCase):
    def test_satisfy(self):
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'lua': {
                        'download': 'http://www.lua.org/ftp/lua-5.2.1.tar.gz',
                        'checksum': '6bb1b0a39b6a5484b71a83323c690154f86b2021',
                        'project': {
                            'make-targets': 'generic',
                            'make-prefix-arg': 'INSTALL_TOP',
                        }
                    }
                }
            }))
        self.assertEqual(self.satisfy(), 0)
        self.assertTrue(os.path.isfile(os.path.join(self.build_directory('lua'), 'include', 'lua.h')))
        self.assertTrue(os.path.isfile(os.path.join(self.build_directory('lua'), 'lib', 'liblua.a')))
