import os
import distutils

from .. import project


class BoostBuildProject(project.Project):

    @staticmethod
    def identifier():
        return 'boostbuild'

    @staticmethod
    def is_valid_project(definition, needy):
        if not definition.target.platform.is_host():
            return False

        if not os.path.isfile('Jamroot'):
            return False

        if os.path.isfile('b2'):
            return True

        return distutils.spawn.find_executable('b2') is not None

    @staticmethod
    def configuration_keys():
        return project.Project.configuration_keys() | {'b2-args'}

    def get_build_concurrency_args(self):
        concurrency = self.build_concurrency()

        if concurrency > 1:
            return ['-j', str(concurrency)]
        elif concurrency == 0:
            return ['-j']
        return []

    def build(self, output_directory):
        b2 = './b2' if os.path.isfile('b2') else 'b2'
        b2_args = self.evaluate(self.configuration('b2-args'))
        b2_args += self.get_build_concurrency_args()
        if self.configuration('linkage') in ['static']:
            b2_args += ['link=static']
        elif self.configuration('linkage') in ['dynamic', 'shared']:
            b2_args += ['link=shared']
        self.command([b2] + b2_args)
        self.command([b2, 'install', '--prefix=%s' % output_directory] + b2_args)
