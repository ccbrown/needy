import os
import subprocess
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

    def test_command_sequence(self):
        if sys.platform == 'win32':
            needy.process.command_sequence(['set FOO=QWERTYUIOP', 'echo %FOO% | findstr "QWERTYUIOP"'])
        else:
            needy.process.command_sequence(['export FOO=QWERTYUIOP', 'echo $FOO | grep "QWERTYUIOP"'])

    def test_command_sequence_failure(self):
        with self.assertRaises(subprocess.CalledProcessError) as a:
            needy.process.command_sequence(['notacommand123123', 'alsonotacommand321'])
