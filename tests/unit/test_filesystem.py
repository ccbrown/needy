import unittest
import os
import tempfile
import shutil
import multiprocessing
import sys

from needy.filesystem import lock_file


class FilesystemTest(unittest.TestCase):
    def test_lock_file_non_blocking(self):
        directory = tempfile.mkdtemp()
        path = os.path.join(directory, 'tempfile')
        try:
            fd = lock_file(path, timeout=0)
            self.assertTrue(fd)
            self.assertFalse(self.try_access_from_other_process(path))
        finally:
            shutil.rmtree(directory)

    @staticmethod
    def try_access_from_other_process(path):
        def run(path):
            fd = lock_file(path, timeout=2)
            sys.exit(0 if fd else 1)
        process = multiprocessing.Process(target=run, args=(path,))
        process.start()
        process.join()
        return process.exitcode == 0

    def test_lock_file_is_exclusive_inside_process(self):
        directory = tempfile.mkdtemp()
        path = os.path.join(directory, 'tempfile')
        try:
            fd = lock_file(path, timeout=2)
            self.assertTrue(fd)
            self.assertFalse(lock_file(path, timeout=0))
        finally:
            shutil.rmtree(directory)
