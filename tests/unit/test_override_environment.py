import unittest
import os

from needy.override_environment import OverrideEnvironment


class OverrideEnvironmentTest(unittest.TestCase):

    def test_basic_usage(self):
        previous_env = os.environ.copy()
        overrides = {
            'PATH': 'foobar'
        }

        with OverrideEnvironment(overrides):
            for var in os.environ:
                self.assertEqual(os.environ[var], 'foobar' if var == 'PATH' else previous_env[var])

        self.assertEqual(os.environ, previous_env)

    def test_add_new_values(self):
        previous_env = os.environ.copy()
        overrides = {
            'FOOBAR': 'foo'
        }

        self.assertFalse('FOOBAR' in os.environ)

        with OverrideEnvironment(overrides):
            for var in os.environ:
                self.assertEqual(os.environ[var], 'foo' if var == 'FOOBAR' else previous_env[var])

        self.assertEqual(os.environ, previous_env)

    def test_unsets_values(self):
        previous_env = os.environ.copy()
        overrides = {
            'PATH': None,
            'FOOBAR': None
        }

        self.assertTrue('PATH' in os.environ)
        self.assertFalse('FOOBAR' in os.environ)

        with OverrideEnvironment(overrides):
            self.assertFalse('PATH' in os.environ)
            self.assertFalse('FOOBAR' in os.environ)
            for var in os.environ:
                self.assertEqual(os.environ[var], previous_env[var])

        self.assertEqual(os.environ, previous_env)
