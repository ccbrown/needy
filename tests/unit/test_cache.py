import unittest

from pyfakefs import fake_filesystem_unittest

from needy.cache import Manifest


class ManifestEntry(unittest.TestCase):
    def test_serialization(self):
        entry = {'use_time': 5}
        self.assertEqual(Manifest.Entry(entry).use_time, 5)
        self.assertEqual(Manifest.Entry().use_time, 0)
        self.assertEqual(entry, Manifest.Entry(entry).to_dict())
        self.assertEqual(Manifest.Entry({'use_time': 0}).to_dict(), dict())


class ManifestTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_load_store_manifest_contents(self):
        path = '/tmp/manifest'
        self.fs.CreateFile(path, contents='{"keys": {"foo": {}}}')

        with Manifest(path) as m:
            self.assertTrue('foo' in m)
            del m['foo']
            m.touch('bar')

        with open(path, 'r') as f:
            self.assertRegexpMatches(f.read(), '{"keys": {"bar": {"use_time": [0-9]*}}}')

    def test_use_time(self):
        path = '/tmp/manifest'
        self.fs.CreateFile(path, contents='{"keys": {"foo": {"use_time": 1234}}}')

        with Manifest(path) as m:
            self.assertEqual(m['foo'].use_time, 1234)
            m['foo'].use_time = 2345

        with open(path, 'r') as f:
            self.assertEqual(f.read(), '{"keys": {"foo": {"use_time": 2345}}}')

    def test_touch(self):
        path = '/tmp/manifest'
        self.fs.CreateFile(path)

        with Manifest(path) as m:
            m.touch('foo')

        with open(path, 'r') as f:
            self.assertRegexpMatches(f.read(), '{"keys": {"foo": {"use_time": [0-9]*}}}')

    def test_remove_key(self):
        path = '/tmp/manifest'
        self.fs.CreateFile(path, contents='{"keys": {"foo": {"use_time": 1234}}}')

        with Manifest(path) as m:
            del m['foo']

        with open(path, 'r') as f:
            self.assertEqual(f.read(), '{"keys": {}}')

    def test_metadata(self):
        path = '/tmp/manifest'
        self.fs.CreateFile(path, contents='{"metadata": {"foo": "bar"}}')

        with Manifest(path) as m:
            self.assertEqual(m.metadata()['foo'], 'bar')
            del m.metadata()['foo']
            m.metadata()['bar'] = 'foo'

        with open(path, 'r') as f:
            content = f.read()
            self.assertRegexpMatches(content, '"keys": {}')
            self.assertRegexpMatches(content, '"metadata": {"bar": "foo"}')
