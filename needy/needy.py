#!/usr/bin/env python

import fnmatch
import json
import os
import subprocess
import multiprocessing
import sys

from collections import OrderedDict

try:
    from colorama import Fore
except ImportError:
    class EmptyStringAttributes:
        def __getattr__(self, name):
            return ''
    Fore = EmptyStringAttributes()

from .library import Library
from .platform import available_platforms, host_platform
from .generator import available_generators
from .target import Target
from .cd import current_directory


class Needy:
    def __init__(self, path, parameters):
        self.__path = path if os.path.isabs(path) else os.path.normpath(os.path.join(current_directory(), path))
        self.__parameters = parameters

        with open(self.__path, 'r') as needs_file:
            self.needs = json.load(needs_file, object_pairs_hook=OrderedDict)

        self.__needs_directory = os.path.join(os.path.dirname(self.__path), 'needs')

    def path(self):
        return self.__path

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

    def command(self, cmd, environment_overrides={}):
        environment_overrides['PWD'] = current_directory()
        env = os.environ.copy()
        env.update(environment_overrides)
        if isinstance(cmd, list):
            subprocess.check_call(cmd, env=env)
        else:
            subprocess.check_call(cmd, env=env, shell=True)

    def command_output(self, cmd, environment_overrides={}):
        environment_overrides['PWD'] = current_directory()
        env = os.environ.copy()
        env.update(environment_overrides)
        with open(os.devnull, 'w') as devnull:
            if isinstance(cmd, list):
                return subprocess.check_output(cmd, env=env, stderr=devnull)
            return subprocess.check_output(cmd, env=env, stderr=devnull, shell=True)

    def recursive(self, needs_file):
        return Needy(needs_file, self.parameters()) if os.path.isfile(needs_file) else None

    def libraries_to_build(self, filters=None):
        if 'libraries' not in self.needs:
            return []

        names = []

        for name, library_configuration in self.needs['libraries'].iteritems():
            if filters:
                match = False
                for filter in filters:
                    if fnmatch.fnmatchcase(name, filter):
                        match = True
                        break
                if not match:
                    continue
            names.append(name)

        graph = {}
        libraries = {}

        while len(names):
            name = names.pop()
            directory = os.path.join(self.__needs_directory, name)
            library = Library(self.needs['libraries'][name], directory, self)
            libraries[name] = library
            if 'dependencies' not in library.configuration():
                graph[name] = set()
                continue
            str_or_list = library.configuration()['dependencies']
            dependencies = str_or_list if isinstance(str_or_list, list) else [str_or_list]
            graph[name] = set(dependencies)
            for dependency in dependencies:
                if dependency not in graph:
                    names.append(dependency)

        s = []

        for name, dependencies in graph.iteritems():
            if len(dependencies) == 0:
                s.append(name)

        ret = []

        while len(s):
            name = s.pop()
            ret.append((name, libraries[name]))
            for n, deps in graph.iteritems():
                if name not in deps:
                    continue
                deps.remove(name)
                if len(deps) == 0:
                    s.append(n)

        for name, deps in graph.iteritems():
            if len(deps):
                raise ValueError('circular dependency detected')

        return ret

    def include_paths(self, target):
        ret = []
        for n, l in self.libraries_to_build():
            if not l.should_build(target):
                continue
            if os.path.isdir(l.include_path(target)):
                ret.append(l.include_path(target))
            needy = self.recursive(os.path.join(l.source_directory(), 'needs.json'))
            if needy:
                ret.extend(needy.include_paths(target))
        return ret

    def library_paths(self, target_or_universal_binary):
        ret = []
        for n, l in self.libraries_to_build():
            if isinstance(target_or_universal_binary, Target):
                if not l.should_build(target_or_universal_binary):
                    continue
                if os.path.isdir(l.library_path(target_or_universal_binary)):
                    ret.append(l.library_path(target_or_universal_binary))
            else:
                ret.append(l.library_path(target_or_universal_binary))
            needy = self.recursive(os.path.join(l.source_directory(), 'needs.json'))
            if needy:
                ret.extend(needy.library_paths(target_or_universal_binary))
        return ret

    def build_directory(self, library, target_or_universal_binary):
        directory = os.path.join(self.__needs_directory, library)
        l = Library(self.needs['libraries'][library], directory, self)
        return l.build_directory(target_or_universal_binary)

    def satisfy_target(self, target, filters=None):
        if 'libraries' not in self.needs:
            return

        print('Satisfying %s' % self.path())

        try:
            for name, library in self.libraries_to_build(filters):
                if library.has_up_to_date_build(target):
                    print(Fore.GREEN + '[UP-TO-DATE]' + Fore.RESET + ' %s' % name)
                else:
                    print(Fore.CYAN + '[OUT-OF-DATE]' + Fore.RESET + ' %s' % name)
                    library.build(target)
                    print(Fore.GREEN + '[SUCCESS]' + Fore.RESET + ' %s' % name)
        except Exception as e:
            print(Fore.RED + '[ERROR]' + Fore.RESET)
            print(e)
            raise

    def satisfy_universal_binary(self, universal_binary, filters=None):
        try:
            print('Satisfying universal binary %s in %s' % (universal_binary, self.path()))

            if 'universal-binaries' not in self.needs:
                raise ValueError('no universal binaries defined')

            if universal_binary not in self.needs['universal-binaries']:
                raise ValueError('unknown universal binary ({})'.format(universal_binary))

            if 'libraries' not in self.needs:
                return

            configuration = self.needs['universal-binaries'][universal_binary]

            for name, library in self.libraries_to_build(filters):
                if library.has_up_to_date_universal_binary(universal_binary, configuration):
                    print(Fore.GREEN + '[UP-TO-DATE]' + Fore.RESET + ' %s' % name)
                else:
                    print(Fore.CYAN + '[OUT-OF-DATE]' + Fore.RESET + ' %s' % name)
                    library.build_universal_binary(universal_binary, configuration)
                    print(Fore.GREEN + '[SUCCESS]' + Fore.RESET + ' %s' % name)
        except Exception as e:
            print(Fore.RED + '[ERROR]' + Fore.RESET)
            print(e)
            raise

    def create_universal_binary(self, inputs, output):
        name, extension = os.path.splitext(output)
        if extension not in ['.a', '.so', '.dylib']:
            return False

        subprocess.check_call(['lipo', '-create'] + inputs + ['-output', output])
        return True

    def generate(self, files):
        if not os.path.exists(self.needs_directory()):
            os.makedirs(self.needs_directory())
        for generator in available_generators():
            if generator.identifier() in files:
                generator().generate(self)
