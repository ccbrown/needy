import unittest
import json
import os

from needy.needy_configuration import NeedyConfiguration
from needy.filesystem import TempDir


class NeedyConfigurationTest(unittest.TestCase):
    def test_recursive_merge(self):
        d = {'build-caches': [{'path': 'foo'}]}
        NeedyConfiguration._recursive_merge(d, {'build-caches': ['bar']})
        NeedyConfiguration._recursive_merge(d, {'build-caches': []})

        self.assertEqual(d, {'build-caches': [{'path': 'foo'}, 'bar']})

    def test_dict_and_list_paths(self):
        with TempDir() as d:
            path = os.path.join(d, 'tmp', 'dir', '.needyconfig')
            os.makedirs(os.path.dirname(path))
            with open(path, 'w') as f:
                f.write(json.dumps({
                    'build-caches': [
                        {'path': 'foo'},
                        {'path': 'bar'},
                        'foobar',
                    ]
                }))

            c = NeedyConfiguration(os.path.dirname(path))

            self.assertEqual(len(c.build_caches()), 3)
            self.assertEqual(c.build_caches()[0].cache().to_dict()['path'], 'foo')
            self.assertEqual(c.build_caches()[1].cache().to_dict()['path'], 'bar')
            self.assertEqual(c.build_caches()[2].cache().to_dict()['path'], 'foobar')

    def test_config_merging(self):
        with TempDir() as d:
            root = os.path.join(d, 'tmp', '.needyconfig')
            leaf = os.path.join(d, 'tmp', 'dir', '.needyconfig')
            os.makedirs(os.path.dirname(leaf))
            with open(root, 'w') as f:
                f.write(json.dumps({'build-caches': ['bar']}))
            with open(leaf, 'w') as f:
                f.write(json.dumps({'build-caches': ['foo']}))

            c = NeedyConfiguration(os.path.dirname(leaf))
            self.assertEqual(len(c.build_caches()), 2)
            self.assertEqual(c.build_caches()[0].cache().to_dict()['path'], 'foo')
            self.assertEqual(c.build_caches()[1].cache().to_dict()['path'], 'bar')

            c = NeedyConfiguration(os.path.dirname(root))
            self.assertEqual(len(c.build_caches()), 1)
            self.assertEqual(c.build_caches()[0].cache().to_dict()['path'], 'bar')

    def test_empty_root_doesnt_effect_leaf(self):
        with TempDir() as d:
            root = os.path.join(d, 'tmp', '.needyconfig')
            leaf = os.path.join(d, 'tmp', 'dir', '.needyconfig')
            os.makedirs(os.path.dirname(leaf))
            with open(root, 'w') as f:
                f.write(json.dumps({'build-caches': []}))
            with open(leaf, 'w') as f:
                f.write(json.dumps({'build-caches': ['foo']}))

            c = NeedyConfiguration(os.path.dirname(leaf))
            self.assertEqual(len(c.build_caches()), 1)
            self.assertEqual(c.build_caches()[0].cache().to_dict()['path'], 'foo')
