import json
import os
import sys

from ..functional_test import TestCase


class GitTest(TestCase):
    def test_source_change(self):
        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'miniupnpc': {
                        'repository': 'https://github.com/miniupnp/miniupnp.git',
                        'commit': 'miniupnpc_1_8',
                        'project': {
                            'build-steps': [
                                'echo noop'
                            ]
                        }
                    }
                }
            }))
        self.assertEqual(self.satisfy(), 0)

        with open(os.path.join(self.path(), 'needs.json'), 'w') as needs_file:
            needs_file.write(json.dumps({
                'libraries': {
                    'miniupnpc': {
                        'repository': 'https://github.com/miniupnp/libnatpmp.git',
                        'commit': '16434170ca6d46c9a92cc99118745e2f43ecae99',
                        'project': {
                            'build-steps': [
                                'echo noop'
                            ]
                        }
                    }
                }
            }))
        self.assertEqual(self.satisfy(), 0)
