import unittest
import os
import tempfile
import shutil
import multiprocessing
import sys

from pyfakefs import fake_filesystem_unittest

from needy.filesystem import lock_file, clean_file, clean_directory, TempDir, dict_file


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
