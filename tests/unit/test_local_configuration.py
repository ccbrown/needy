import multiprocessing
import os
import sys
import tempfile
import unittest

from needy.local_configuration import LocalConfiguration


class LocalConfigurationTest(unittest.TestCase):
    def test_locking(self):
        file = tempfile.NamedTemporaryFile(delete=True)
        try:
            self.assertTrue(LocalConfigurationTest.try_access_from_another_process(file.name))
            with LocalConfiguration(file.name) as config:
                self.assertIsNotNone(config)
                self.assertFalse(LocalConfigurationTest.try_access_from_another_process(file.name))
            self.assertTrue(LocalConfigurationTest.try_access_from_another_process(file.name))
        finally:
            file.close()

    @staticmethod
    def try_access_from_another_process(path):
        def run(path):
            with LocalConfiguration(path, blocking=False) as config:
                sys.exit(0 if config is not None else 1)
        process = multiprocessing.Process(target=run, args=(path,))
        process.start()
        process.join()
        return process.exitcode == 0
