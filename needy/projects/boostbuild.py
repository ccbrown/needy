import os
import distutils
import sys

from .. import project


class BoostBuildProject(project.Project):

    @staticmethod
    def identifier():
        return 'boostbuild'

    @staticmethod
    def is_valid_project(definition, needy):
        return os.path.isfile('Jamroot')

    @staticmethod
    def missing_prerequisites(definition, needy):
        return ['b2'] if not os.path.isfile('bootstrap.sh') and distutils.spawn.find_executable('b2') is None else []

    @staticmethod
    def configuration_keys():
        return project.Project.configuration_keys() | {'b2-args', 'bootstrap-args'}

    def get_build_concurrency_args(self):
        concurrency = self.build_concurrency()

        if concurrency > 1:
            return ['-j', str(concurrency)]
        elif concurrency == 0:
            return ['-j']
        return []

    def configure(self, build_directory):
        bootstrap_args = self.evaluate(self.configuration('bootstrap-args'))
        if not os.path.isfile('bootstrap.sh'):
            if len(bootstrap_args) > 0:
                raise RuntimeError('bootstrap-args was given, but no bootstrap script is present')
            return

        self.command(['./bootstrap.sh'] + bootstrap_args, use_target_overrides=False)

    def build(self, output_directory):
        b2 = './b2' if os.path.isfile('b2') else 'b2'
        b2_args = self.evaluate(self.configuration('b2-args'))
        b2_args.extend(self.get_build_concurrency_args())

        b2_args.append('architecture={}'.format('arm' if 'arm' in self.target().architecture else 'x86'))
        b2_args.append('address-model={}'.format('64' if '64' in self.target().architecture else '32'))

        if self.target().platform in ['ios', 'iossimulator', 'tvos', 'tvossimulator']:
            b2_args.append('target-os=iphone')
        elif self.target().platform == 'android':
            b2_args.append('target-os=android')

        toolset = 'darwin' if sys.platform == 'darwin' else ('clang' if distutils.spawn.find_executable('clang') is not None else 'gcc')
        b2_args.append('toolset={}-needy'.format(toolset))

        project_config = ''
        if os.path.exists('project-config.jam'):
            with open('project-config.jam', 'r') as f:
                project_config = f.read()

        if ' : needy : [ os.environ CC ] ;' not in project_config:
            project_config = "import os ;\nusing {} : needy : [ os.environ CC ] ;\n".format(toolset) + project_config
            with open('project-config.jam', 'w') as f:
                f.write(project_config)

        self.command([b2, 'install', '--prefix={}'.format(output_directory)] + b2_args)
