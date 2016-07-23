import os
import shutil
import tempfile
import unittest

from needy.__main__ import main
from needy.cd import cd
from needy.needy import Needy
from needy.platform import host_platform
from needy.target import Target


class TestCase(unittest.TestCase):
    def setUp(self):
        self.__path = tempfile.mkdtemp()
        return self

    def tearDown(self):
        shutil.rmtree(self.__path)

    def path(self):
        return self.__path

    def satisfy(self):
        return self.execute(['satisfy'])

    def execute(self, command):
        with cd(self.path()):
            return main(['needy'] + command)

    def build_directory(self, library, target_or_universal_binary=Target(host_platform()())):
        needy = Needy(self.path())
        return needy.build_directory(library, target_or_universal_binary)

    def needs_directory(self):
        needy = Needy(self.path())
        return needy.needs_directory()
