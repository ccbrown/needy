import multiprocessing
import os
import sys
import unittest

from needy.filesystem import TempDir
from needy.local_configuration import LocalConfiguration


def try_locking_local_config(path):
    with LocalConfiguration(path, blocking=False) as config:
        sys.exit(0 if config is not None else 1)


class LocalConfigurationTest(unittest.TestCase):
    def test_locking(self):
        with TempDir() as temp_dir:
            config_file = os.path.join(temp_dir, 'config')
            self.assertTrue(LocalConfigurationTest.try_access_from_another_process(config_file))
            with LocalConfiguration(config_file) as config:
                self.assertIsNotNone(config)
                self.assertFalse(LocalConfigurationTest.try_access_from_another_process(config_file))
            self.assertTrue(LocalConfigurationTest.try_access_from_another_process(config_file))

    def test_development_mode_persistence(self):
        with TempDir() as temp_dir:
            config_file = os.path.join(temp_dir, 'config')
            with LocalConfiguration(config_file) as config:
                self.assertFalse(config.development_mode('test'))
                config.set_development_mode('test', True)
                self.assertTrue(config.development_mode('test'))
            with LocalConfiguration(config_file) as config:
                self.assertTrue(config.development_mode('test'))
                config.set_development_mode('test', False)
                self.assertFalse(config.development_mode('test'))

    @staticmethod
    def try_access_from_another_process(path):
        process = multiprocessing.Process(target=try_locking_local_config, args=(path,))
        process.start()
        process.join()
        return process.exitcode == 0
