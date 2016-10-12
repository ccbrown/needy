import distutils.spawn
import os
import shutil

from .. import project
from ..platforms.windows import WindowsPlatform

from .source import SourceProject


class MSBuildProject(project.Project):

    @staticmethod
    def identifier():
        return 'msbuild'

    @staticmethod
    def is_valid_project(definition, needy):
        if not isinstance(definition.target.platform, WindowsPlatform):
            return False, 'target platform not an MSBuild supported platform'

        if 'msbuild-project' not in definition.configuration:
            extensions = [os.path.splitext(f)[1] for f in os.listdir('.') if os.path.isfile(f)]
            if not set(['.vcproj', '.vcxproj', '.sln']) & set(extensions):
                return False, 'no projects or solutions present'

        return True, 'msbuild and a valid project are present'

    @staticmethod
    def missing_prerequisites(definition, needy):
        return ['msbuild'] if not distutils.spawn.find_executable('msbuild') else []

    @staticmethod
    def configuration_keys():
        return project.Project.configuration_keys() | {
            'header-directory', 'msbuild-project', 'msbuild-properties'
        }

    def build(self, output_directory):
        properties = {
            'Configuration': 'Release',
            'OutDir': output_directory
        }

        if self.configuration('msbuild-properties'):
            for key, value in self.configuration('msbuild-properties').items():
                properties[key] = self.evaluate(value)

        msbuild_args = ['/maxcpucount:{}'.format(self.build_concurrency())]
        msbuild_args.extend(['/p:{}={}'.format(key, value) for key, value in properties.items()])

        if self.configuration('msbuild-project'):
            msbuild_args.append(self.configuration('msbuild-project'))

        self.command(['msbuild'] + msbuild_args)

        include_directory = os.path.join(output_directory, 'include')
        lib_directory = os.path.join(output_directory, 'lib')

        lib_extensions = ['.lib']

        if not os.path.exists(lib_directory):
            os.makedirs(lib_directory)

        for file in os.listdir(output_directory):
            name, extension = os.path.splitext(file)
            if extension in lib_extensions:
                shutil.move(os.path.join(output_directory, file), lib_directory)

        if not os.listdir(include_directory):
            SourceProject.copy_headers(self.directory(), self.configuration(), include_directory)
