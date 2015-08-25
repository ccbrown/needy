import os
import subprocess

from .. import project
from ..cd import cd


class CMakeProject(project.Project):

    @staticmethod
    def identifier():
        return 'cmake'

    @staticmethod
    def is_valid_project(definition):
        return definition.target.platform.identifier() == 'host' and os.path.isfile('CMakeLists.txt')

    def configure(self, output_directory):
        cmake_directory = os.path.join(self.directory(), 'cmake')
        if not os.path.exists(cmake_directory):
            os.makedirs(cmake_directory)
        with cd(cmake_directory):
            subprocess.check_call(['cmake', '-G', 'Unix Makefiles', '-DCMAKE_INSTALL_PREFIX=%s' % output_directory, self.directory()])

    def build(self, output_directory):
        cmake_directory = os.path.join(self.directory(), 'cmake')
        with cd(cmake_directory):
            subprocess.check_call(['make', 'install/local'])
