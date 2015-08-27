import os
import subprocess

from .. import project


class BoostBuildProject(project.Project):

    @staticmethod
    def identifier():
        return 'boostbuild'

    @staticmethod
    def is_valid_project(definition, needy):
        if definition.target.platform.identifier() != 'host':
            return False
            
        if not os.path.isfile('Jamroot'):
            return False
        
        if os.path.isfile('b2'):
            return True

        try:
            needy.command_output(['b2', '-v'])
            return True
        except subprocess.CalledProcessError:
            return False
        except OSError:
            return False

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
        b2_args = self.evaluate(self.configuration('b2-args'), output_directory)
        b2_args += self.get_build_concurrency_args()
        self.command([b2] + b2_args)
        self.command([b2, 'install', '--prefix=%s' % output_directory] + b2_args)
