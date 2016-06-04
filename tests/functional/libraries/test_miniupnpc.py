import json
import os

from ..functional_test import TestCase


class MiniUPNPCTest(TestCase):
    def test_satisfy(self):
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'miniupnpc': {
                        'repository': 'https://github.com/miniupnp/miniupnp.git',
                        'commit': 'miniupnpc_1_8',
                        'project': {
                            'root': 'miniupnpc',
                            'make-targets': 'upnpc-static'
                        }
                    }
                }
            }))
        self.assertEqual(self.satisfy(), 0)
        self.assertTrue(os.path.isfile(os.path.join(self.build_directory('miniupnpc'), 'include', 'miniupnpc', 'miniupnpc.h')))
        self.assertTrue(os.path.isfile(os.path.join(self.build_directory('miniupnpc'), 'lib', 'libminiupnpc.a')))
