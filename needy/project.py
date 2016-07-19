import os
import sys
import logging

from .process import command
from .process import command_output


def evaluate_conditionals(configuration, target):
    should_continue = True
    while should_continue:
        if 'conditionals' not in configuration:
            return configuration

        copy = configuration.copy()
        copy.pop('conditionals')
        should_continue = False

        for key, cases in configuration['conditionals'].items():
            values = []
            if key == 'platform':
                values.append(target.platform.identifier())
                if target.platform.is_host():
                    values.append('host')
                    values.append(sys.platform)
            elif key == 'architecture':
                values.append(target.architecture)
            else:
                raise ValueError('unknown conditional key')

            for case, config in cases.items():
                if case in values or (case[0] == '!' and case[1:] not in values) or case == '*':
                    should_continue = True
                    copy.update(config)
                    break

        configuration = copy

    return configuration


class ProjectDefinition:
    def __init__(self, target, directory, configuration={}):
        self.target = target
        self.directory = directory
        self.configuration = configuration


class Project:
    def __init__(self, definition, needy):
        self.__definition = definition
        self.needy = needy

    @staticmethod
    def identifier():
        raise NotImplementedError('Subclasses of Project must override identifier')

    @staticmethod
    def is_valid_project(definition, needy):
        raise NotImplementedError('Subclasses of Project must override is_valid_project')

    @staticmethod
    def missing_prerequisites(definition, needy):
        return []

    @staticmethod
    def configuration_keys():
        """ should return a set of configuration keys that this project uses """
        return {'pre-build', 'post-build', 'max-concurrency'}

    def target(self):
        return self.__definition.target

    def directory(self):
        return self.__definition.directory

    def configuration(self, key=None):
        if key is None:
            return self.__definition.configuration
        if key in self.__definition.configuration:
            return self.__definition.configuration[key]
        return None

    def build_concurrency(self):
        concurrency = self.needy.build_concurrency()
        if self.configuration('max-concurrency') is not None:
            concurrency = min(concurrency, self.configuration('max-concurrency'))
        return concurrency

    def set_string_format_variables(self, **kwargs):
        self.__string_format_variables = kwargs

    def evaluate(self, str_or_list):
        l = [] if not str_or_list else (str_or_list if isinstance(str_or_list, list) else [str_or_list])
        return [str.format(**self.__string_format_variables) for str in l]

    def run_commands(self, commands):
        for command in self.evaluate(commands):
            self.command(command)

    def target_environment_overrides(self):
        ret = {}

        needy_wrappers = os.path.join(self.directory(), 'needy-wrappers')

        if 'CC' in os.environ:
            ret['HOST_CC'] = os.environ.get('HOST_CC', os.environ['CC'])
        if self.target().platform.c_compiler(self.target().architecture):
            ret['CC'] = os.path.join(needy_wrappers, 'needy-cc')

        if 'CXX' in os.environ:
            ret['HOST_CXX'] = os.environ.get('HOST_CXX', os.environ['CXX'])
        if self.target().platform.cxx_compiler(self.target().architecture):
            ret['CXX'] = os.path.join(needy_wrappers, 'needy-cxx')

        if 'LDFLAGS' in os.environ:
            ret['HOST_LDFLAGS'] = os.environ.get('HOST_LDFLAGS', os.environ['LDFLAGS'])
        libraries = self.target().platform.libraries(self.target().architecture)
        if len(libraries) > 0:
            ret['LDFLAGS'] = ' '.join(libraries + ([os.environ['LDFLAGS']] if 'LDFLAGS' in os.environ else []))

        ret['HOST_PATH'] = os.environ.get('HOST_PATH', os.environ['PATH'])
        binary_paths = [needy_wrappers] + self.target().platform.binary_paths(self.target().architecture)
        if len(binary_paths) > 0:
            ret['PATH'] = ('%s:%s' % (':'.join(binary_paths), os.environ['PATH']))

        return ret

    def setup(self):
        # create wrappers for cc / cxx since some systems (e.g. boost's bootstrap) expect these to be single tokens
        c_compiler = self.target().platform.c_compiler(self.target().architecture)
        if c_compiler:
            self.__create_wrapper('needy-cc', c_compiler)
        cxx_compiler = self.target().platform.cxx_compiler(self.target().architecture)
        if cxx_compiler:
            self.__create_wrapper('needy-cxx', cxx_compiler)

        # prefer to stick within the version of python we were invoked with
        if sys.executable:
            self.__create_wrapper('python', sys.executable)

    def pre_build(self, output_directory):
        build_dirs = [os.path.join(output_directory, d) for d in ['include', 'lib']]
        self.__create_directories(build_dirs)
        self.run_commands(self.configuration('pre-build'))

    def configure(self, build_directory):
        pass

    def post_build(self, output_directory):
        self.run_commands(self.configuration('post-build'))

    def __create_directories(self, dirs):
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def __create_wrapper(self, name, command):
        if not os.path.exists('needy-wrappers'):
            os.makedirs('needy-wrappers')

        path = 'needy-wrappers/{}'.format(name)
        with open(path, 'w') as f:
            f.write("#!/bin/sh\n{} \"$@\"".format(command))
        os.chmod(path, 0o755)

    def command(self, cmd, verbosity=logging.INFO, environment_overrides={}, use_target_overrides=True):
        env = environment_overrides.copy()
        if use_target_overrides:
            env.update(self.target_environment_overrides())
        else:
            for var in ['PATH', 'CC', 'CXX', 'LDFLAGS']:
                if 'HOST_'+var in os.environ:
                    env[var] = os.environ['HOST_'+var]
        command(cmd, environment_overrides=env)

    def command_output(self, arguments, verbosity=logging.INFO, environment_overrides={}):
        return command_output(arguments, environment_overrides=environment_overrides)
