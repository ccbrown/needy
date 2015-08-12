import os
import shlex
import subprocess

# TODO: reevaluate where this function belongs
def evaluate_conditionals(configuration, target):
    if 'conditionals' not in configuration:
        return configuration

    ret = configuration.copy()

    for conditional in configuration['conditionals']:
        is_true = True
        for key, value in conditional.iteritems():
            if not is_true:
                break

            if key == 'true' or key == 'false':
                continue

            if key == 'platform':
                if isinstance(value, list):
                    is_true = target.platform.identifier() in value
                else:
                    is_true = target.platform.identifier() == value
            else:
                raise ValueError('unknown conditional key')

        if is_true:
            if 'true' in conditional:
                ret.update(conditional['true'])
        elif 'false' in conditional:
            ret.update(conditional['false'])

    return ret


class ProjectDefinition:
    def __init__(self, target, directory, configuration):
        self.target = target
        self.directory = directory
        self.configuration = configuration


class Project:
    def __init__(self, definition, needy):
        self.__definition = definition
        self.needy = needy

    @staticmethod
    def is_valid_project(definition):
        raise NotImplementedError('Subclasses of Project must override is_valid_project')

    def target(self):
        return self.__definition.target

    def directory(self):
        return self.__definition.directory

    def configuration(self, key=None):
        if key == None:
            return self.__definition.configuration
        if key in self.__definition.configuration:
            return self.__definition.configuration[key]
        return None

    def build_concurrency(self):
        concurrency = self.needy.build_concurrency()
        if self.configuration('max-concurrency') is not None:
            concurrency = min(concurrency, self.configuration('max-concurrency'))
        return concurrency

    def pre_build(self, output_directory):
        pre_build_commands = self.configuration('pre-build') or []
        for command in pre_build_commands:
            subprocess.check_call(shlex.split(command))
        needs_file = os.path.join(self.directory(), 'needs.json')
        if os.path.isfile(needs_file):
            from needy import Needy
            recursive_needy = Needy(needs_file, self.needy.parameters())
            recursive_needy.satisfy_target(self.target())

    def configure(self, build_directory):
        pass

    def post_build(self, output_directory):
        postbuild_commands = self.configuration('post-build') or []
        for command in postbuild_commands:
            subprocess.check_call(shlex.split(command.format(build_directory=output_directory)))
