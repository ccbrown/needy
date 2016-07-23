import os
import sys
import unittest

import needy.process


class ProcessTest(unittest.TestCase):

    def test_list_command_output(self):
        self.assertEqual('hello', needy.process.command_output([sys.executable, '-c', 'print(\'hello\')']).strip())

    def test_shell_command_output(self):
        if sys.platform == 'win32':
            self.assertEqual(os.getcwd(), needy.process.command_output('echo %CD%').strip())
        else:
            self.assertEqual('hello', needy.process.command_output('printf `printf hello`'))
