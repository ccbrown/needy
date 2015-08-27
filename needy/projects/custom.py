import os
import subprocess

from .. import project
from ..cd import cd

from .make import get_make_jobs_args


class CustomProject(project.Project):

    @staticmethod
    def identifier():
        return 'custom'

    @staticmethod
    def is_valid_project(definition, needy):
        return True

    @staticmethod
    def configuration_keys():
        return ['configure-steps', 'build-steps']

    def configure(self, output_directory):
        self.run_commands(self.configuration('configure-steps') or [], output_directory)

    def build(self, output_directory):
        self.run_commands(self.configuration('build-steps') or [], output_directory)
