import unittest
import os
import shutil

from time import sleep

from needy.build_cache import BuildCache
from needy.filesystem import TempDir
from needy.caches.directory import Directory
from needy.cache import SourceNotFound, KeyNotFound


class BuildCacheTest(unittest.TestCase):
    def test_creates_manifest_if_necessary(self):
        with TempDir() as cache_dir:
            build_cache = BuildCache(Directory(path=cache_dir))

            with TempDir() as build_dir:
                open(os.path.join(build_dir, 'foo'), 'a').close()
                self.assertTrue(os.listdir(build_dir))
                build_cache.store_artifacts(build_dir, 'foo')
                self.assertTrue(os.listdir(cache_dir))

    def test_store_load_artifacts(self):
        with TempDir() as cache_dir:
            build_cache = BuildCache(Directory(path=cache_dir))

            with TempDir() as build_dir:
                for name in ['f1', 'f2', 'dir1/f3']:
                    path = os.path.join(build_dir, name)
                    try:
                        os.makedirs(os.path.dirname(path))
                    except:
                        pass
                    with open(path, 'w') as f:
                        f.write(name)

                build_cache.store_artifacts(build_dir, 'foo')

            with TempDir() as temp:
                build_cache.load_artifacts('foo', os.path.join(temp, 'build_dir'))
                for name in ['f1', 'f2', 'dir1/f3']:
                    path = os.path.join(temp, 'build_dir', name)
                    with open(path, 'r') as f:
                        self.assertEqual(f.read(), name)

    def test_store_adds_entries_to_manifest(self):
        with TempDir() as cache_dir:
            build_cache = BuildCache(Directory(path=cache_dir))

            self.assertTrue('foo' not in build_cache.manifest())

            with TempDir() as build_dir:
                build_cache.store_artifacts(build_dir, 'foo')

            self.assertTrue('foo' in build_cache.manifest())

    def test_store_raises_with_invalid_source(self):
        with TempDir() as cache_dir:
            build_cache = BuildCache(Directory(path=cache_dir))

            self.assertRaises(SourceNotFound, lambda: build_cache.store_artifacts(os.path.join(cache_dir, 'doesnt_exist'), 'foo'))

    def test_load_raises_with_invalid_key(self):
        with TempDir() as cache_dir:
            build_cache = BuildCache(Directory(path=cache_dir))

            with TempDir() as d:
                self.assertRaises(KeyNotFound, lambda: build_cache.load_artifacts('foo', os.path.join(d, 'dest')))

    def test_load_policy_creates_cache_policies(self):
        with TempDir() as cache_dir, TempDir() as d:
            build_cache = BuildCache(Directory(path=cache_dir), lifetime=5)
            build_cache._load_policies()
            self.assertTrue(BuildCache.policy_key() in os.listdir(cache_dir))

        with TempDir() as cache_dir, TempDir() as d:
            build_cache = BuildCache(Directory(path=cache_dir))
            build_cache._load_policies()
            self.assertTrue(BuildCache.policy_key() in os.listdir(cache_dir))

        with TempDir() as cache_dir, TempDir() as d:
            build_cache = BuildCache(Directory(path=os.path.join(cache_dir, 'cache')))
            build_cache._load_policies()
            self.assertTrue(BuildCache.policy_key() in os.listdir(os.path.join(cache_dir, 'cache')))

    def test_load_increases_lifetime(self):
        with TempDir() as cache_dir, TempDir() as d:
            build_cache = BuildCache(Directory(path=cache_dir), lifetime=5)

            build_cache.store_artifacts(d, 'foo')
            previous_use_time = build_cache.manifest()['foo'].use_time

            self.assertNotEqual(previous_use_time, 0)
            sleep(3)

            build_cache.load_artifacts('foo', os.path.join(d, 'temp'))
            self.assertGreater(build_cache.manifest()['foo'].use_time, previous_use_time)

    def test_garbage_collection(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = BuildCache(Directory(path=cache_dir), lifetime=2, gc_frequency=0)

            cache.store_artifacts(d, 'foo_key')
            self.assertTrue('foo_key' in os.listdir(cache_dir))
            sleep(4)

            cache.store_artifacts(d, 'bar_key')
            self.assertFalse('foo_key' in os.listdir(cache_dir))
            self.assertTrue('bar_key' in os.listdir(cache_dir))
            sleep(4)
