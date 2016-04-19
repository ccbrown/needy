import unittest

import needy.process


class ProcessTest(unittest.TestCase):

    def test_list_command_output(self):
        self.assertEqual('hello', needy.process.command_output(['printf', 'hello']))

    def test_shell_command_output(self):
        self.assertEqual('hello', needy.process.command_output('printf `printf hello`'))
