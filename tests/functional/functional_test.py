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
        with cd(self.path()):
            return main(['needy', 'satisfy'])

    def build_directory(self, library):
        needy = Needy(self.path())
        return needy.build_directory(library, Target(host_platform()()))
