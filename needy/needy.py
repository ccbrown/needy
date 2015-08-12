#!/usr/bin/env python

import json
import os
import subprocess
import multiprocessing

from colorama import Fore

from library import Library
from platform import available_platforms
from target import Target


class Needy:
    def __init__(self, path, parameters):
        self.__path = path
        self.__parameters = parameters

        with open(self.__path, 'r') as needs_file:
            self.needs = json.load(needs_file)

        self.__needs_directory = os.path.join(os.path.dirname(self.__path), 'needs')

    def path(self):
        return self.__path

    def parameters(self):
        return self.__parameters

    def build_concurrency(self):
        if self.parameters().build_concurrency > 0:
            return self.parameters().build_concurrency
        return multiprocessing.cpu_count()

    def platform(self, identifier):
        for platform in available_platforms():
            if identifier == platform.identifier():
                return platform(self.__parameters)
        raise ValueError('unknown platform')

    def target(self, identifier):
        parts = identifier.split(':')
        platform = self.platform(parts[0])
        return Target(platform, parts[1] if len(parts) > 1 else platform.default_architecture())

    def command(self, arguments, environment_overrides=None):
        env = None
        if environment_overrides:
            env = os.environ.copy()
            env.update(environment_overrides)
        subprocess.check_call(arguments, env=env)

    def libraries_to_build(self, target):
        if 'libraries' not in self.needs:
            return []

        ret = []

        for name, library_configuration in self.needs['libraries'].iteritems():
            directory = os.path.join(self.__needs_directory, name)
            library = Library(library_configuration, directory, self)
            if library.should_build(target):
                ret.append((name, library))

        return ret

    def include_paths(self, target):
        return [l.include_path(target) for n, l in self.libraries_to_build(target)]

    def library_paths(self, target):
        return [l.library_path(target) for n, l in self.libraries_to_build(target)]

    def satisfy_target(self, target):
        if 'libraries' not in self.needs:
            return

        print 'Satisfying %s' % self.path()

        try:
            for name, library_configuration in self.needs['libraries'].iteritems():
                directory = os.path.join(self.__needs_directory, name)
                library = Library(library_configuration, directory, self)
                if library.has_up_to_date_build(target):
                    print Fore.GREEN + '[UP-TO-DATE]' + Fore.RESET + ' %s' % name
                else:
                    print Fore.CYAN + '[OUT-OF-DATE]' + Fore.RESET + ' %s' % name
                    library.build(target)
                    print Fore.GREEN + '[SUCCESS]' + Fore.RESET + ' %s' % name
        except Exception as e:
            print Fore.RED + '[ERROR]' + Fore.RESET, e
            raise

    def satisfy_universal_binary(self, universal_binary):
        try:
            print 'Satisfying universal binary %s in %s' % (universal_binary, self.path())

            if 'universal-binaries' not in self.needs:
                raise ValueError('no universal binaries defined')

            if universal_binary not in self.needs['universal-binaries']:
                raise ValueError('unknown universal binary')

            if 'libraries' not in self.needs:
                return

            configuration = self.needs['universal-binaries'][universal_binary]

            for name, library_configuration in self.needs['libraries'].iteritems():
                directory = os.path.join(self.__needs_directory, name)
                library = Library(library_configuration, directory, self)
                if library.has_up_to_date_universal_binary(universal_binary, configuration):
                    print Fore.GREEN + '[UP-TO-DATE]' + Fore.RESET + ' %s' % name
                else:
                    print Fore.CYAN + '[OUT-OF-DATE]' + Fore.RESET + ' %s' % name
                    library.build_universal_binary(universal_binary, configuration)
                    print Fore.GREEN + '[SUCCESS]' + Fore.RESET + ' %s' % name
        except Exception as e:
            print Fore.RED + '[ERROR]' + Fore.RESET, e
            raise

    def create_universal_binary(self, inputs, output):
        name, extension = os.path.splitext(output)
        if extension not in ['.a', '.so', '.dylib']:
            return False

        subprocess.check_call(['lipo', '-create'] + inputs + ['-output', output])
        return True
