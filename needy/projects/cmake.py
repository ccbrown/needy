import os

from .. import project
from ..cd import cd


class CMakeProject(project.Project):

    @staticmethod
    def identifier():
        return 'cmake'

    @staticmethod
    def is_valid_project(definition, needy):
        return definition.target.platform.identifier() == 'host' and os.path.isfile('CMakeLists.txt')

    def configure(self, output_directory):
        cmake_directory = os.path.join(self.directory(), 'cmake')
        if not os.path.exists(cmake_directory):
            os.makedirs(cmake_directory)
        with cd(cmake_directory):
            self.command(['cmake', '-G', 'Unix Makefiles', '-DCMAKE_INSTALL_PREFIX=%s' % output_directory, self.directory()])

    def build(self, output_directory):
        cmake_directory = os.path.join(self.directory(), 'cmake')
        with cd(cmake_directory):
            self.command(['make', 'install/local'])
