import os
import subprocess

from .. import project

class BoostBuildProject(project.Project):

    @staticmethod
    def is_valid_project(definition):
        return definition.target.platform.identifier() is 'host' and os.path.isfile('Jamroot') and (os.path.isfile('b2') or subprocess.check_output(['b2', '-v']))

    def build(self, output_directory):
        b2 = './b2' if os.path.isfile('b2') else 'b2'
        b2_args = self.configuration('b2-args') or []
        subprocess.check_call([b2] + b2_args)
        subprocess.check_call([b2, 'install', '--prefix=%s' % output_directory] + b2_args)