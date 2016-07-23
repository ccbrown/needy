import unittest
import os
import shutil
import multiprocessing
import sys

from needy.caches.directory import Directory
from needy.cache import SourceNotFound, KeyNotFound
from needy.filesystem import TempDir


def try_cache_key_lock(cache_dir, key):
    cache = Directory(path=cache_dir)
    try:
        cache.lock_key(key, timeout=0)
        cache.unlock_key(key)
    except:
        sys.exit(1)
    sys.exit(0)


class DirectoryTest(unittest.TestCase):
    def test_file_store_load(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = Directory(path=cache_dir)

            foo_file = os.path.join(d, 'foo_file')
            bar_file = os.path.join(d, 'bar_file')

            with open(foo_file, 'w') as f:
                f.write('foo')
            with open(bar_file, 'w') as f:
                f.write('bar')

            self.assertFalse(os.listdir(cache_dir))

            cache.store_file(foo_file, 'foo_key')
            cache.store_file(bar_file, 'bar_key')

            self.assertTrue(os.listdir(cache_dir))

            os.remove(foo_file)
            os.remove(bar_file)

            cache.load_file('foo_key', foo_file)
            cache.load_file('bar_key', bar_file)

            with open(foo_file, 'r') as f:
                self.assertEqual(f.read(), 'foo')
            with open(bar_file, 'r') as f:
                self.assertEqual(f.read(), 'bar')

    def test_directory_store_load(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = Directory(path=cache_dir)

            foo_file = os.path.join(d, 'foo_file')
            bar_file = os.path.join(d, 'bar_file')

            with open(foo_file, 'w') as f:
                f.write('foo')
            with open(bar_file, 'w') as f:
                f.write('bar')

            self.assertFalse(os.listdir(cache_dir))

            cache.store_directory(d, 'foo_key')

            self.assertTrue(os.listdir(cache_dir))

            shutil.rmtree(d)

            cache.load_directory('foo_key', d)

            with open(foo_file, 'r') as f:
                self.assertEqual(f.read(), 'foo')
            with open(bar_file, 'r') as f:
                self.assertEqual(f.read(), 'bar')

    def test_store_raise_error_on_invalid_path(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = Directory(path=cache_dir)

            not_file = os.path.join(d, 'doesnt_exist')
            self.assertRaises(SourceNotFound, lambda: cache.store_file(not_file, 'key'))

    def test_load_raise_error_on_invalid_key(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = Directory(path=cache_dir)

            destination = os.path.join(d, 'build_directory')
            self.assertRaises(KeyNotFound, lambda: cache.load_file('key', destination))

    def test_key_lock_unlock(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = Directory(path=cache_dir)

            foo_file = os.path.join(d, 'foo_file')
            with open(foo_file, 'w') as f:
                f.write('foo')
            key = 'foo_key'
            cache.store_file(foo_file, key)

            self.assertTrue(self.try_lock_from_another_process(cache_dir, key))

            with cache.lease(key):
                self.assertFalse(self.try_lock_from_another_process(cache_dir, key))

            self.assertTrue(self.try_lock_from_another_process(cache_dir, key))

    def test_key_lock_creates(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = Directory(path=cache_dir)

            key = 'foo_key'
            self.assertFalse(cache.exists(key))

            with cache.lease(key, create=True):
                self.assertTrue(cache.exists(key))

            self.assertTrue(cache.exists(key))
            self.assertTrue(os.listdir(cache_dir))

    @staticmethod
    def try_lock_from_another_process(cache_dir, key):
        process = multiprocessing.Process(target=try_cache_key_lock, args=(cache_dir, key,))
        process.start()
        process.join()
        return process.exitcode == 0

    def test_key_exists(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = Directory(path=cache_dir)

            foo_file = os.path.join(d, 'foo_file')
            with open(foo_file, 'w') as f:
                f.write('foo')
            key = 'foo_key'

            self.assertFalse(cache.exists(key))
            cache.store_file(foo_file, key)
            self.assertTrue(cache.exists(key))

    def test_key_unset(self):
        with TempDir() as cache_dir, TempDir() as d:
            cache = Directory(path=cache_dir)

            foo_file = os.path.join(d, 'foo_file')
            with open(foo_file, 'w') as f:
                f.write('foo')
            key = 'foo_key'
            cache.store_file(foo_file, key)

            self.assertTrue(cache.exists(key))
            cache.unset_key(key)
            self.assertFalse(cache.exists(key))

    def test_raises_with_key_lock_unlock_on_invalid_path(self):
        with TempDir() as cache_dir:
            cache = Directory(path=cache_dir)
            self.assertRaises(KeyNotFound, lambda: cache.lock_key('doesntexist'))
            self.assertRaises(KeyNotFound, lambda: cache.unlock_key('doesntexist'))

    def test_lease_file(self):
        with TempDir() as cache_dir:
            cache = Directory(path=cache_dir)

            key = 'foo'

            self.assertFalse(cache.exists(key))

            with cache.lease_file(key, create=True) as path:
                self.assertTrue(cache.exists(key))
                self.assertTrue(os.path.exists(path))
                with open(path, 'r') as f:
                    self.assertNotEqual(f.read(), key)
                with open(path, 'w') as f:
                    f.write(key)

            self.assertTrue(cache.exists(key))

            with cache.lease_file(key) as path:
                with open(path, 'r') as f:
                    self.assertEqual(f.read(), key)
