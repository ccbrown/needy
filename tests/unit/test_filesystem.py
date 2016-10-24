import unittest
import os
import tempfile
import shutil
import multiprocessing
import sys
import binascii
import hashlib

from pyfakefs import fake_filesystem_unittest

from needy.filesystem import lock_file, clean_file, clean_directory, TempDir, dict_file, copy_if_changed, file_hash


def try_file_lock(path):
    fd = lock_file(path, timeout=2)
    sys.exit(0 if fd else 1)


class FilesystemTest(unittest.TestCase):
    def test_lock_file_non_blocking(self):
        with TempDir() as d:
            path = os.path.join(d, 'tempfile')
            fd = lock_file(path, timeout=0)
            self.assertTrue(fd)
            self.assertFalse(self.try_access_from_other_process(path))
            os.close(fd)

    @staticmethod
    def try_access_from_other_process(path):
        process = multiprocessing.Process(target=try_file_lock, args=(path,))
        process.start()
        process.join()
        return process.exitcode == 0


class FakeFilesystemTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_clean_directory_creates_parents(self):
        clean_directory(os.path.join('tmp', 'dirty-dir'))

        self.assertTrue(os.path.exists(os.path.join('tmp', 'dirty-dir')))
        self.assertFalse(os.listdir(os.path.join('tmp', 'dirty-dir')))

    def test_clean_directory_removes_contents(self):
        self.fs.CreateFile(os.path.join('tmp', 'dirty-dir', 'file1'))
        self.fs.CreateFile(os.path.join('tmp', 'dirty-dir', 'file2'))
        self.fs.CreateDirectory(os.path.join('tmp', 'dirty-dir', 'dir1'))
        self.fs.CreateFile(os.path.join('tmp', 'dirty-dir', 'dir1', 'file3'))
        clean_directory(os.path.join('tmp', 'dirty-dir'))

        self.assertTrue(os.path.exists(os.path.join('tmp', 'dirty-dir')))
        self.assertFalse(os.listdir(os.path.join('tmp', 'dirty-dir')))

    def test_clean_file_creates_parents(self):
        clean_file(os.path.join('tmp', 'dirty-dir', 'file'))

        self.assertTrue(os.path.exists(os.path.join('tmp', 'dirty-dir')))
        self.assertFalse(os.listdir(os.path.join('tmp', 'dirty-dir')))

    def test_clean_file_removes_file(self):
        self.fs.CreateFile(os.path.join('tmp', 'dirty-dir', 'file1'))
        self.fs.CreateFile(os.path.join('tmp', 'dirty-dir', 'file2'))
        self.fs.CreateDirectory(os.path.join('tmp', 'dirty-dir', 'dir1'))
        self.fs.CreateFile(os.path.join('tmp', 'dirty-dir', 'dir1', 'file3'))
        clean_file(os.path.join('tmp', 'dirty-dir', 'file1'))

        self.assertTrue(os.path.exists(os.path.join('tmp', 'dirty-dir')))
        self.assertEqual(set(os.listdir(os.path.join('tmp', 'dirty-dir'))), set(['file2', 'dir1']))

    def test_temp_dir(self):
        path = ''
        with TempDir() as d:
            path = d
            self.assertTrue(os.path.exists(path))
            self.assertFalse(os.listdir(path))
        self.assertFalse(os.path.exists(path))

    def test_file_dict_load_store(self):
        self.fs.CreateFile(os.path.join('tmp', 'file'), contents='{"foo": 1}')

        with dict_file(os.path.join('tmp', 'file')) as d:
            self.assertEqual(d['foo'], 1)
            del d['foo']
            d['bar'] = 'test'

        with open(os.path.join('tmp', 'file')) as f:
            self.assertEqual(f.read(), '{"bar": "test"}')

    def test_file_dict_creates_file(self):
        self.fs.CreateDirectory('tmp')

        with dict_file(os.path.join('tmp', 'file')) as d:
            d['bar'] = 'test'

        with open(os.path.join('tmp', 'file')) as f:
            self.assertEqual(f.read(), '{"bar": "test"}')

    def test_file_hash(self):
        self.fs.CreateFile(os.path.join('file'), contents='foo')
        foo_hash = b'2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae'

        with open('file', 'rb') as f:
            self.assertEqual(binascii.hexlify(file_hash(f, hashlib.sha256())), foo_hash)

    def test_copy_if_changed(self):
        file1 = self.fs.CreateFile(os.path.join('file1'), contents='foo')

        file2 = self.fs.CreateFile(os.path.join('file2'), contents='foo')
        file3 = self.fs.CreateFile(os.path.join('file3'), contents='bar')

        file1.st_mtime = 1
        file2.st_mtime = 2
        file3.st_mtime = 3

        copy_if_changed('file2', 'file1')

        self.assertEqual(os.path.getmtime('file1'), 1)

        with open('file1', 'r') as f:
            self.assertEqual(f.read(), 'foo')

        copy_if_changed('file3', 'file1')

        self.assertEqual(os.path.getmtime('file1'), 3)

        with open('file1', 'r') as f:
            self.assertEqual(f.read(), 'bar')

    def test_copy_if_changed_directory_destination(self):
        self.fs.CreateFile(os.path.join('tmp', 'foo'), contents='foo')
        self.fs.CreateFile('foo', contents='bar')

        copy_if_changed('foo', 'tmp')

        with open(os.path.join('tmp', 'foo'), 'r') as f:
            self.assertEqual(f.read(), 'bar')
