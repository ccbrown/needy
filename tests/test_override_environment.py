import unittest
import os

from needy.override_environment import OverrideEnvironment


class OverrideEnvironmentTest(unittest.TestCase):

    def test_basic_usage(self):
        previous_env = os.environ.copy()
        overrides = {'PATH': 'foobar'}

        with OverrideEnvironment(overrides):
            for var in os.environ:
                self.assertEqual(os.environ[var], 'foobar' if var == 'PATH' else previous_env[var])

        self.assertEqual(os.environ, previous_env)
