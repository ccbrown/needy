import distutils
import os

from .. import project
from ..cd import cd


class CMakeProject(project.Project):

    @staticmethod
    def identifier():
        return 'cmake'

    @staticmethod
    def configuration_keys():
        return project.Project.configuration_keys() | {'cmake-options'}

    @staticmethod
    def is_valid_project(definition, needy):
        return definition.target.platform.is_host() and os.path.isfile('CMakeLists.txt')

    @staticmethod
    def missing_prerequisites(definition, needy):
        return ['cmake'] if distutils.spawn.find_executable('cmake') is None else []

    def configure(self, output_directory):
        cmake_directory = os.path.join(self.directory(), 'cmake')
        if not os.path.exists(cmake_directory):
            os.makedirs(cmake_directory)
        cmake_options = self.configuration('cmake-options') or []
        cmake_option_strings = ['-D{}={}'.format(key, self.evaluate(self.__cmake_value(value))[0]) for key, value in cmake_options.items()] if cmake_options else []
        with cd(cmake_directory):
            self.command(['cmake', '-G', 'Unix Makefiles'] + cmake_option_strings + ['-DCMAKE_INSTALL_PREFIX=%s' % output_directory, self.directory()])

    def build(self, output_directory):
        cmake_directory = os.path.join(self.directory(), 'cmake')
        with cd(cmake_directory):
            self.command(['make', 'install'])

    @staticmethod
    def __cmake_value(value):
        if isinstance(value, bool):
            return 'ON' if value else 'OFF'
        return str(value)
