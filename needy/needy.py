import datetime
import distutils.spawn
import fnmatch
import json
import logging
import multiprocessing
import os
import re
import subprocess
import sys

from collections import OrderedDict
from contextlib import contextmanager

from .process import command_output
from .library import Library
from .universal_binary import UniversalBinary
from .platforms import available_platforms, host_platform
from .generators import available_generators
from .target import Target
from .cd import current_directory
from .local_configuration import LocalConfiguration
from .needy_configuration import NeedyConfiguration
from .memoize import MemoizeMethod
from .utility import log_section, Fore, Style


@contextmanager
def ConfiguredNeedy(scope, parameters=None):
    needs_directory = Needy.resolve_needs_directory(scope)
    if needs_directory is None:
        raise RuntimeError('No needs file found!')
    with LocalConfiguration(os.path.join(needs_directory, 'config.json')) as local_configuration:
        yield Needy(scope, parameters, local_configuration=local_configuration, needy_configuration=NeedyConfiguration(scope))


class Needy:
    def __init__(self, path='.', parameters={}, local_configuration=None, needy_configuration=None):
        self.__path = self.__normalize_path(path)
        self.__parameters = parameters

        self.__needs_file = self.find_needs_file(self.__path)
        self.__needs_directory = Needy.resolve_needs_directory(self.__path)

        self.__local_configuration = local_configuration

        if self.__needs_file is None:
            raise RuntimeError('No needs file found in {}'.format(self.__path))

        self.__needy_configuration = needy_configuration

        logging.debug('Using needs file {}'.format(self.__needs_file))
        logging.debug('Using needs directory {}'.format(self.__needs_directory))

    @staticmethod
    def resolve_needs_directory(directory):
        directory = Needy.__normalize_path(directory)

        ret = None
        parent_needs = None
        while directory:
            if Needy.find_needs_file(directory):
                if ret is None:
                    ret = os.path.join(directory, 'needs')
                else:
                    parent_needs = os.path.join(directory, 'needs')
                    break

            parent = os.path.dirname(directory)
            if directory == os.sep or directory == parent:
                break
            directory = parent

        if ret is None:
            return None

        if parent_needs:
            real_needs_directory = os.path.dirname(ret)
            while real_needs_directory != '/':
                split = os.path.split(real_needs_directory)
                if split[0] == parent_needs:
                    real_needs_directory = os.path.join(real_needs_directory, 'needs')
                    break
                real_needs_directory = split[0]
            if real_needs_directory != '/':
                if not os.path.isdir(real_needs_directory):
                    os.makedirs(real_needs_directory)
                if not os.path.exists(ret):
                    # If ret is a broken symlink, os.path.exists returns false
                    # and we need to remove the broken symlink before trying to
                    # relink it.
                    if os.path.islink(ret):
                        os.unlink(ret)
                    os.symlink(real_needs_directory, ret)

        return ret

    def path(self):
        return self.__path

    def needs_file(self):
        return self.__needs_file

    @staticmethod
    def find_needs_file(directory):
        directory = Needy.__normalize_path(directory)
        ret = None
        for name in ['needs.json', 'needs.yaml']:
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                if ret:
                    raise RuntimeError('More than one needs file is present.')
                ret = path
        return ret

    def development_mode_libraries(self):
        return [name for name in self.__local_configuration.library_names() if self.__local_configuration.development_mode(name)]

    def set_development_mode(self, library_name, enable=True):
        if not os.path.isdir(self.source_directory(library_name)):
            raise RuntimeError('Please initialize the library before enabling development mode.')

        was_already = self.__local_configuration.development_mode(library_name) == enable
        self.__local_configuration.set_development_mode(library_name, enable)

        if enable:
            print('Development mode {}enabled for {}: {}'.format('already ' if was_already else '', library_name, self.source_directory(library_name)))
        else:
            print('Development mode {}disabled for {}. Please ensure that you have persisted any changes you wish to keep.'.format('already ' if was_already else '', library_name))

    def needy_configuration(self):
        '''Not to be confused with needs_configuration'''
        return self.__needy_configuration

    @MemoizeMethod
    def needs_configuration(self, target=None):
        rendered = self.render(target=target)

        name, extension = os.path.splitext(self.needs_file())

        if extension == '.json':
            return json.loads(rendered, object_pairs_hook=OrderedDict)

        if extension == '.yaml':
            try:
                import yaml

                class OrderedLoader(yaml.SafeLoader):
                    pass

                def construct_mapping(loader, node):
                    loader.flatten_mapping(node)
                    return OrderedDict(loader.construct_pairs(node))

                OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
                return yaml.load(rendered, OrderedLoader)
            except ImportError:
                raise RuntimeError('The needs are defined in a YAML file. Please install the pyyaml Python package.')

            return None

        raise RuntimeError('No needs file found.')

    def render(self, target=None):
        ''' return rendered needs from needs file '''
        source = ''
        with open(self.needs_file(), 'r') as needs_file:
            source = needs_file.read()

        return self.__render(source, target=target)

    @MemoizeMethod
    def __render(self, source, target=None):
        try:
            from jinja2 import Environment, PackageLoader
            env = Environment()
            env.filters['dirname'] = os.path.dirname
            env.filters['json_escape'] = lambda s: json.dumps(s)[1:][:-1]
            if hasattr(self.__parameters, 'define') and self.__parameters.define:
                for defines in self.__parameters.define:
                    for define in defines:
                        parts = define.split('=', 1)
                        value = parts[1] if len(parts) >= 2 else 1
                        env.globals[parts[0]] = value
            template = env.from_string(source)
            if getattr(self, '_needs_configuration_first_pass', None):
                source = self._needs_configuration_first_pass
            else:
                variables = {
                    'env': os.environ,
                    'platform': target.platform.identifier() if target else None,
                    'architecture': target.architecture if target else None,
                    'host_platform': host_platform().identifier(),
                    'needs_file': self.needs_file(),
                    'needs_directory': self.needs_directory(),
                    'build_directory': lambda library, target_override=None: None
                }
                self._needs_configuration_first_pass = template.render(**variables)
                try:
                    variables['build_directory'] = lambda library, target_override=None: self.build_directory(library, self.target(target_override) if target_override else target) if target else None
                    source = template.render(**variables)
                finally:
                    self._needs_configuration_first_pass = None
        except ImportError:
            if re.compile('{%.*%}').search(source) or re.compile('{{.*}}').search(source) or re.compile('{#.*#}').search(source):
                raise RuntimeError('The needs file appears to contain Jinja templating. Please install the jinja2 Python package.')
        return source

    def needs_directory(self):
        return self.__needs_directory

    def need_directory(self, name):
        return os.path.join(self.needs_directory(), name)

    def parameters(self):
        return self.__parameters

    def build_concurrency(self):
        if getattr(self.parameters(), 'concurrency', 0) > 0:
            return self.parameters().concurrency
        return multiprocessing.cpu_count()

    def platform(self, identifier):
        platform = host_platform() if identifier == 'host' else available_platforms().get(identifier, None)
        if platform is not None:
            return platform(self.__parameters)

        raise ValueError('unknown platform (%s)' % identifier)

    def target(self, identifier):
        parts = identifier.split(':')
        platform = self.platform(parts[0])
        return Target(platform, parts[1] if len(parts) > 1 else platform.default_architecture())

    @classmethod
    def test_filters(cls, name, filters):
        for filter in filters:
            if fnmatch.fnmatchcase(name, filter):
                return True
        return False

    def library(self, target, name):
        development_mode = self.__local_configuration and self.__local_configuration.development_mode(name)
        return Library(self, name,
                       target=target,
                       configuration=self.library_configuration(target, name),
                       development_mode=development_mode,
                       build_caches=self.needy_configuration().build_caches() if self.needy_configuration() else [])

    def library_configuration(self, target, name):
        return self.needs_configuration(target)['libraries'][name] if name in self.needs_configuration(target)['libraries'] else None

    @classmethod
    def pkgconfig_package_is_present(cls, name):
        if not distutils.spawn.find_executable('pkg-config'):
            return False
        env = os.environ.copy()
        env['PKG_CONFIG_LIBDIR'] = ''
        return subprocess.call(['pkg-config', name, '--exists'], env=env) == 0

    @classmethod
    def library_is_overridden(cls, name):
        return cls.pkgconfig_package_is_present(name)

    def libraries_to_build(self, target, filters=None, include_dependencies=True):
        """ returns a list of (name, library) tuples for libraries that should be built by needy, in the order that they should be built in """
        needs_configuration = self.needs_configuration(target)

        if 'libraries' not in needs_configuration:
            return []

        names = []

        for name, library_configuration in needs_configuration['libraries'].items():
            if filters and not self.test_filters(name, filters):
                continue
            names.append(name)

        graph = {}
        libraries = {}

        while len(names):
            name = names.pop()
            library = self.library(target, name)
            libraries[name] = library
            if 'dependencies' not in library.configuration() or not include_dependencies:
                graph[name] = set()
                continue
            dependencies = library.dependencies()
            dependencies_to_build = [dependency for dependency in dependencies if not self.library_is_overridden(dependency)]
            graph[name] = set(dependencies_to_build)
            for dependency in dependencies_to_build:
                if dependency not in graph:
                    names.append(dependency)

        s = []

        for name, dependencies in graph.items():
            if len(dependencies) == 0:
                s.append(name)

        ret = []

        while len(s):
            name = s.pop()
            ret.append((name, libraries[name]))
            for n, deps in graph.items():
                if name not in deps:
                    continue
                deps.remove(name)
                if len(deps) == 0:
                    s.append(n)

        for name, deps in graph.items():
            if len(deps):
                raise ValueError('circular dependency detected')

        return ret

    def universal_binary_configuration(self, universal_binary):
        needs_configuration = self.needs_configuration()

        if 'universal-binaries' not in needs_configuration:
            raise ValueError('no universal binaries defined')

        if universal_binary not in needs_configuration['universal-binaries']:
            raise ValueError('unknown universal binary ({})'.format(universal_binary))

        return needs_configuration['universal-binaries'][universal_binary]

    def universal_binary_names(self):
        return self.needs_configuration().get('universal-binaries', {}).keys()

    def libraries(self, target_or_universal_binary, filters=None, include_dependencies=True):
        ''' Libraries and dependent libraries. Dependent libraries may not match the filters. '''
        libraries = dict()
        targets = []

        if isinstance(target_or_universal_binary, Target):
            targets = [target_or_universal_binary]
        else:
            configuration = self.universal_binary_configuration(target_or_universal_binary)
            for platform, architectures in configuration.items():
                for architecture in architectures:
                    targets.append(Target(self.platform(platform), architecture))

        for target in targets:
            for name, library in self.libraries_to_build(target, filters, include_dependencies=include_dependencies):
                if name not in libraries:
                    libraries[name] = list()
                libraries[name].append(library)

        return libraries

    def include_paths(self, target_or_universal_binary, filters=None):
        ret = []
        for name, libraries in self.libraries(target_or_universal_binary, filters).items():
            if isinstance(target_or_universal_binary, Target):
                for library in libraries:
                    ret.append(library.include_path())
            else:
                ub = UniversalBinary(target_or_universal_binary, libraries, self)
                ret.append(ub.include_path())
        return ret

    def library_paths(self, target_or_universal_binary, filters=None):
        ret = []
        for name, libraries in self.libraries(target_or_universal_binary, filters).items():
            if isinstance(target_or_universal_binary, Target):
                for library in libraries:
                    ret.append(library.library_path())
            else:
                ub = UniversalBinary(target_or_universal_binary, libraries, self)
                ret.append(ub.library_path())
        return ret

    def pkg_config_path(self, target_or_universal_binary, filters=None):
        return ':'.join(self.pkg_config_paths(target_or_universal_binary, filters))

    def pkg_config_paths(self, target_or_universal_binary, filters=None):
        return [os.path.join(path, 'pkgconfig') for path in self.library_paths(target_or_universal_binary, filters)]

    def build_directory(self, library, target_or_universal_binary):
        if isinstance(target_or_universal_binary, Target):
            return self.library(target_or_universal_binary, library).build_directory()
        l = Library(self, library)
        b = UniversalBinary(target_or_universal_binary, [l], self)
        return b.build_directory()

    def source_directory(self, library_name):
        return os.path.join(self.need_directory(library_name), 'source')

    def satisfy_target(self, target, filters=None):
        needs_configuration = self.needs_configuration(target)

        if 'libraries' not in needs_configuration:
            return

        print('Satisfying {} in {}'.format(target, self.path()))

        try:
            for name, library in self.libraries_to_build(target, filters):
                if not self.parameters().force_build and library.is_up_to_date():
                    self.__print_status(Fore.GREEN, 'UP-TO-DATE', name)
                else:
                    with log_section('needy.satisfy.{}'.format(name)):
                        self.__print_status(Fore.CYAN, 'OUT-OF-DATE', name)
                        start_time = datetime.datetime.now()
                        library.build()
                    self.__print_status(Fore.GREEN, 'SUCCESS', '{} in {}'.format(name, datetime.datetime.now() - start_time))
        except Exception as e:
            self.__print_status(Fore.RED, 'ERROR')
            print(e)
            raise

    def satisfy_universal_binary(self, universal_binary, filters=None):
        try:
            print('Satisfying universal binary {} in {}'.format(universal_binary, self.path()))
            configuration = self.universal_binary_configuration(universal_binary)

            libraries = dict()

            for platform, architectures in configuration.items():
                for architecture in architectures:
                    target = Target(self.platform(platform), architecture)
                    self.satisfy_target(target, filters)
                    for name, library in self.libraries_to_build(target, filters):
                        if name not in libraries:
                            libraries[name] = list()
                        libraries[name].append(library)

            for name, libs in libraries.items():
                if filters and not self.test_filters(name, filters):
                    continue
                binary = UniversalBinary(universal_binary, libs, self)
                if not self.parameters().force_build and binary.is_up_to_date():
                    self.__print_status(Fore.GREEN, 'UP-TO-DATE', name)
                else:
                    with log_section('needy.satisfy.{}'.format(name)):
                        self.__print_status(Fore.CYAN, 'OUT-OF-DATE', name)
                        start_time = datetime.datetime.now()
                        binary.build()
                    self.__print_status(Fore.GREEN, 'SUCCESS', '{} in {}'.format(name, datetime.datetime.now() - start_time))
        except Exception as e:
            self.__print_status(Fore.RED, 'ERROR')
            print(e)
            raise

    def initialize(self, target, filters=None):
        needs_configuration = self.needs_configuration(target)

        if 'libraries' not in needs_configuration:
            return

        for name, libraries in self.libraries(target, filters, include_dependencies=False).items():
            assert len(libraries) == 1
            logging.info('Initializing {}...'.format(name))
            libraries[0].initialize_source()

    def clean(self, target, filters=None, only_build_directory=False, force=False):
        libs = list(self.libraries(target, filters, include_dependencies=False).items())
        for name, libraries in libs:
            assert len(libraries) == 1
            if self.__local_configuration.development_mode(name) and not force:
                if len(libs) == 1:
                    raise RuntimeError('{} is in development mode; cannot clean without force'.format(name))
                else:
                    logging.info('{} is in development mode; cannot clean without force'.format(name))
                    continue
            logging.info('Cleaning {}...'.format(name))
            libraries[0].clean_build()
            if only_build_directory:
                continue
            libraries[0].clean_source()

    def synchronize(self, target, filters=None):
        if 'libraries' not in self.needs_configuration(target):
            return

        dev_mode_libraries = self.development_mode_libraries()

        libraries_to_sync = []

        for name, libraries in self.libraries(target, filters, include_dependencies=False).items():
            if filters and name not in dev_mode_libraries:
                raise RuntimeError('{} does not have development mode enabled'.format(name))
            elif name in dev_mode_libraries:
                libraries_to_sync.append((name, libraries))

        if len(libraries_to_sync) == 0:
            logging.warning('no libraries have development mode enabled')

        for name, libraries in libraries_to_sync:
            assert len(libraries) == 1
            logging.info('Synchronizing {}...'.format(name))
            libraries[0].synchronize_source()

    @staticmethod
    def __normalize_path(path):
        return path if os.path.isabs(path) else os.path.normpath(os.path.join(current_directory(), path))

    def __print_status(self, color, status, name=None):
        print(color + Style.BRIGHT + '[' + status + ']' + Style.RESET_ALL + Fore.RESET + (' %s' % name if name else ''))

    def generate(self, files):
        if not os.path.exists(self.needs_directory()):
            os.makedirs(self.needs_directory())
        for generator in available_generators():
            if generator.identifier() in files:
                generator().generate(self)
