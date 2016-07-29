import fnmatch
import json
import os
import multiprocessing
import re
import sys
import logging

from collections import OrderedDict

try:
    from colorama import Fore
    from colorama import Style
except ImportError:
    class EmptyStringAttributes:
        def __getattr__(self, name):
            return ''
    Fore = EmptyStringAttributes()
    Style = EmptyStringAttributes()

from .process import command_output
from .library import Library
from .universal_binary import UniversalBinary
from .platform import available_platforms, host_platform
from .generator import available_generators
from .target import Target
from .cd import current_directory
from .needy_configuration import NeedyConfiguration


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

    def development_mode(self, library_name):
        return self.__local_configuration.development_mode(library_name)

    def set_development_mode(self, library_name, enable=True):
        if not os.path.isdir(os.path.join(self.__needs_directory, library_name)):
            raise RuntimeError('Please build the library once before enabling development mode.')

        was_already = self.__local_configuration.development_mode(library_name) == enable
        self.__local_configuration.set_development_mode(library_name, enable)

        if enable:
            print('Development mode {}enabled for {}: {}'.format('already ' if was_already else '', library_name, self.source_directory(library_name)))
        else:
            print('Development mode {}disabled for {}. Please ensure that you have persisted any changes you wish to keep.'.format('already ' if was_already else '', library_name))

    def needy_configuration(self):
        '''Not to be confused with needs_configuration'''
        return self.__needy_configuration

    def needs_configuration(self, target=None):
        configuration = ''
        with open(self.needs_file(), 'r') as needs_file:
            configuration = needs_file.read()

        try:
            from jinja2 import Environment, PackageLoader
            env = Environment()
            env.filters['dirname'] = os.path.dirname
            if hasattr(self.__parameters, 'define') and self.__parameters.define:
                for defines in self.__parameters.define:
                    for define in defines:
                        parts = define.split('=', 1)
                        value = parts[1] if len(parts) >= 2 else 1
                        env.globals[parts[0]] = value
            template = env.from_string(configuration)
            configuration = template.render(
                platform=target.platform.identifier() if target else None,
                architecture=target.architecture if target else None,
                host_platform=host_platform().identifier(),
                needs_file=self.needs_file(),
                needs_directory=self.needs_directory(),
                build_directory=lambda library, target_override=None: self.build_directory(library, self.target(target_override) if target_override else target) if target else None
            )
        except ImportError:
            if re.compile('{%.*%}').search(configuration) or re.compile('{{.*}}').search(configuration) or re.compile('{#.*#}').search(configuration):
                raise RuntimeError('The needs file appears to contain Jinja templating. Please install the jinja2 Python package.')

        name, extension = os.path.splitext(self.needs_file())

        if extension == '.json':
            return json.loads(configuration, object_pairs_hook=OrderedDict)

        if extension == '.yaml':
            try:
                import yaml

                class OrderedLoader(yaml.SafeLoader):
                    pass

                def construct_mapping(loader, node):
                    loader.flatten_mapping(node)
                    return OrderedDict(loader.construct_pairs(node))

                OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
                return yaml.load(configuration, OrderedLoader)
            except ImportError:
                raise RuntimeError('The needs are defined in a YAML file. Please install the pyyaml Python package.')

            return None

        raise NotImplementedError('file parsing not implemented')

    def needs_directory(self):
        return self.__needs_directory

    def parameters(self):
        return self.__parameters

    def build_concurrency(self):
        if self.parameters().concurrency > 0:
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

    def libraries_to_build(self, target, filters=None):
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
            development_mode = self.__local_configuration and self.__local_configuration.development_mode(name)
            library = Library(self, name,
                              target=target,
                              configuration=needs_configuration['libraries'][name],
                              development_mode=development_mode,
                              build_caches=self.needy_configuration().build_caches())
            libraries[name] = library
            if 'dependencies' not in library.configuration():
                graph[name] = set()
                continue
            dependencies = library.dependencies()
            graph[name] = set(dependencies)
            for dependency in dependencies:
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

    def libraries(self, target_or_universal_binary, filters=None):
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
            for name, library in self.libraries_to_build(target, filters):
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
            l = Library(self, library, target=target_or_universal_binary)
            return l.build_directory()
        l = Library(self, library)
        b = UniversalBinary(target_or_universal_binary, [l], self)
        return b.build_directory()

    def source_directory(self, library_name):
        return os.path.join(self.__needs_directory, library_name, 'source')

    def satisfy_target(self, target, filters=None):
        needs_configuration = self.needs_configuration(target)

        if 'libraries' not in needs_configuration:
            return

        print('Satisfying needs in %s' % self.path())

        try:
            for name, library in self.libraries_to_build(target, filters):
                if library.has_up_to_date_build():
                    self.__print_status(Fore.GREEN, 'UP-TO-DATE', name)
                else:
                    self.__print_status(Fore.CYAN, 'OUT-OF-DATE', name)
                    library.build()
                    self.__print_status(Fore.GREEN, 'SUCCESS', name)
        except Exception as e:
            self.__print_status(Fore.RED, 'ERROR')
            print(e)
            raise

    def satisfy_universal_binary(self, universal_binary, filters=None):
        try:
            print('Satisfying universal binary %s in %s' % (universal_binary, self.path()))
            configuration = self.universal_binary_configuration(universal_binary)

            libraries = dict()

            for platform, architectures in configuration.items():
                for architecture in architectures:
                    target = Target(self.platform(platform), architecture)
                    for name, library in self.libraries_to_build(target, filters):
                        if name not in libraries:
                            libraries[name] = list()
                        libraries[name].append(library)
                        if library.has_up_to_date_build():
                            self.__print_status(Fore.GREEN, 'UP-TO-DATE', '{} for {} {}'.format(name, target.platform.identifier(), target.architecture))
                        else:
                            self.__print_status(Fore.CYAN, 'OUT-OF-DATE', name)
                            library.build()
                            self.__print_status(Fore.GREEN, 'SUCCESS', name)

            for name, libs in libraries.items():
                if filters and not self.test_filters(name, filters):
                    continue
                binary = UniversalBinary(universal_binary, libs, self)
                if binary.is_up_to_date():
                    self.__print_status(Fore.GREEN, 'UP-TO-DATE', name)
                else:
                    self.__print_status(Fore.CYAN, 'OUT-OF-DATE', name)
                    binary.build()
                    self.__print_status(Fore.GREEN, 'SUCCESS', name)
        except Exception as e:
            self.__print_status(Fore.RED, 'ERROR')
            print(e)
            raise

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
