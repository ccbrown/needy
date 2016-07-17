import unittest
import os
import tempfile
import shutil
import multiprocessing
import sys

from pyfakefs import fake_filesystem_unittest

from needy.filesystem import lock_file, clean_file, clean_directory, TempDir, dict_file


class FilesystemTest(unittest.TestCase):
    def test_lock_file_non_blocking(self):
        with TempDir() as d:
            path = os.path.join(d, 'tempfile')
            fd = lock_file(path, timeout=0)
            self.assertTrue(fd)
            self.assertFalse(self.try_access_from_other_process(path))

    @staticmethod
    def try_access_from_other_process(path):
        def run(path):
            fd = lock_file(path, timeout=2)
            sys.exit(0 if fd else 1)
        process = multiprocessing.Process(target=run, args=(path,))
        process.start()
        process.join()
        return process.exitcode == 0

    def test_lock_file_shares_exclusive_lock_inside_process(self):
        with TempDir() as d:
            path = os.path.join(d, 'tempfile')
            fd = lock_file(path, timeout=2)
            self.assertTrue(fd)
            os.close(fd)
            self.assertTrue(lock_file(path, timeout=0))


class FakeFilesystemTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_clean_directory_creates_parents(self):
        clean_directory('/tmp/dirty-dir')

        self.assertTrue(os.path.exists('/tmp/dirty-dir'))
        self.assertFalse(os.listdir('/tmp/dirty-dir'))

    def test_clean_directory_removes_contents(self):
        self.fs.CreateFile('/tmp/dirty-dir/file1')
        self.fs.CreateFile('/tmp/dirty-dir/file2')
        self.fs.CreateDirectory('/tmp/dirty-dir/dir1')
        self.fs.CreateFile('/tmp/dirty-dir/dir1/file3')
        clean_directory('/tmp/dirty-dir')

        self.assertTrue(os.path.exists('/tmp/dirty-dir'))
        self.assertFalse(os.listdir('/tmp/dirty-dir'))

    def test_clean_file_creates_parents(self):
        clean_file('/tmp/dirty-dir/file')

        self.assertTrue(os.path.exists('/tmp/dirty-dir'))
        self.assertFalse(os.listdir('/tmp/dirty-dir'))

    def test_clean_file_removes_file(self):
        self.fs.CreateFile('/tmp/dirty-dir/file1')
        self.fs.CreateFile('/tmp/dirty-dir/file2')
        self.fs.CreateDirectory('/tmp/dirty-dir/dir1')
        self.fs.CreateFile('/tmp/dirty-dir/dir1/file3')
        clean_file('/tmp/dirty-dir/file1')

        self.assertTrue(os.path.exists('/tmp/dirty-dir'))
        self.assertEqual(set(os.listdir('/tmp/dirty-dir')), set(['file2', 'dir1']))

    def test_temp_dir(self):
        path = ''
        with TempDir() as d:
            path = d
            self.assertTrue(os.path.exists(path))
            self.assertFalse(os.listdir(path))
        self.assertFalse(os.path.exists(path))

    def test_file_dict_load_store(self):
        self.fs.CreateFile('/tmp/file', contents='{"foo": 1}')

        with dict_file('/tmp/file') as d:
            self.assertEqual(d['foo'], 1)
            del d['foo']
            d['bar'] = 'test'

        with open('/tmp/file') as f:
            self.assertEqual(f.read(), '{"bar": "test"}')

    def test_file_dict_creates_file(self):
        self.fs.CreateDirectory('/tmp')

        with dict_file('/tmp/file') as d:
            d['bar'] = 'test'

        with open('/tmp/file') as f:
            self.assertEqual(f.read(), '{"bar": "test"}')
