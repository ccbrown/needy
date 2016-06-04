import os

from .. import project
from ..cd import cd


class CustomProject(project.Project):

    @staticmethod
    def identifier():
        return 'custom'

    @staticmethod
    def is_valid_project(definition, needy):
        return True, 'custom projects are always valid'

    @staticmethod
    def configuration_keys():
        return project.Project.configuration_keys() | {'configure-steps', 'build-steps'}

    def configure(self, output_directory):
        self.run_commands(self.configuration('configure-steps') or [])

    def build(self, output_directory):
        self.run_commands(self.configuration('build-steps') or [])
