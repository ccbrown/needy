import os
import shlex


def evaluate_conditionals(configuration, target):
    if 'conditionals' not in configuration:
        return configuration

    ret = configuration.copy()

    for key, cases in configuration['conditionals'].iteritems():
        value = None
        if key == 'platform':
            value = target.platform.identifier()
        else:
            raise ValueError('unknown conditional key')

        for case, config in cases.iteritems():
            if case == value or (case[0] == '!' and case != '!{}'.format(value)):
                ret.update(config)

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
    def identifier():
        raise NotImplementedError('Subclasses of Project must override identifier')

    @staticmethod
    def is_valid_project(definition, needy):
        raise NotImplementedError('Subclasses of Project must override is_valid_project')

    @staticmethod
    def configuration_keys():
        """ should return a list of configuration keys that this project uses """
        return []

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

    def project_targets(self):
        return self.configuration('targets') or []

    def evaluate(self, str_or_list, build_directory):
        l = [] if not str_or_list else (str_or_list if isinstance(str_or_list, list) else [str_or_list])
        return [str.format(build_directory=build_directory, 
                           platform=self.target().platform.identifier(), 
                           architecture=self.target().architecture) for str in l]

    def run_commands(self, commands, build_directory):
        for command in self.evaluate(commands, build_directory):
            self.command(shlex.split(command))

    def environment_overrides(self):
        ret = {}

        c_compiler = self.target().platform.c_compiler(self.target().architecture)
        if c_compiler:
            ret['CC'] = c_compiler

        cxx_compiler = self.target().platform.cxx_compiler(self.target().architecture)
        if cxx_compiler:
            ret['CXX'] = cxx_compiler

        libraries = self.target().platform.libraries(self.target().architecture)
        if len(libraries) > 0:
            ret['LDFLAGS'] = ' '.join(libraries)

        binary_paths = self.target().platform.binary_paths(self.target().architecture)
        if len(binary_paths) > 0:
            ret['PATH'] = ('%s:%s' % (':'.join(binary_paths), os.environ['PATH']))

        return ret

    def pre_build(self, output_directory):
        self.run_commands(self.configuration('pre-build'), output_directory)

    def configure(self, build_directory):
        pass

    def post_build(self, output_directory):
        self.run_commands(self.configuration('post-build'), output_directory)

    def command(self, arguments, environment_overrides={}):
        env = environment_overrides.copy()
        env.update(self.environment_overrides())
        self.needy.command(arguments, environment_overrides=env)

    def command_output(self, arguments, environment_overrides={}):
        return self.needy.command_output(arguments, environment_overrides=environment_overrides)
