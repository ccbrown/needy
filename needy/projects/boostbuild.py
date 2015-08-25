import os
import subprocess

from .. import project


class BoostBuildProject(project.Project):

    @staticmethod
    def identifier():
        return 'boostbuild'

    @staticmethod
    def is_valid_project(definition):
        return definition.target.platform.identifier() == 'host' and os.path.isfile('Jamroot') and (os.path.isfile('b2') or subprocess.check_output(['b2', '-v']))

    @staticmethod
    def configuration_keys():
        return ['b2-args']

    def get_build_concurrency_args(self):
        concurrency = self.build_concurrency()

        if concurrency > 1:
            return ['-j', str(concurrency)]
        elif concurrency == 0:
            return ['-j']
        return []

    def build(self, output_directory):
        b2 = './b2' if os.path.isfile('b2') else 'b2'
        b2_args = self.configuration('b2-args') or []
        b2_args += self.get_build_concurrency_args()
        subprocess.check_call([b2] + b2_args)
        subprocess.check_call([b2, 'install', '--prefix=%s' % output_directory] + b2_args)
