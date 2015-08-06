#!/usr/bin/env python

import json
import os
import subprocess
import sys

from colorama import Fore

from library import Library
from platform import available_platforms
from target import Target

class Needy:
    def __init__(self, path, parameters):
        self.path = path
        self.parameters = parameters

        with open(self.path, 'r') as needs_file:
            self.needs = json.load(needs_file)

        self.needs_directory = os.path.join(os.path.dirname(self.path), 'needs')
    
    def platform(self, identifier):
        for platform in available_platforms():
            if identifier == platform.identifier():
                return platform(self.parameters)
        raise ValueError('unknown platform')

    def command(self, arguments, environment_overrides = None):
        env = None
        if environment_overrides:
            env = os.environ.copy()
            env.update(environment_overrides)
        subprocess.check_call(arguments, env = env)

    def satisfy_target(self, target):
        if not 'libraries' in self.needs:
            return

        try:
            print 'Building libraries for %s %s' % (target.platform.identifier(), target.architecture)
    
            for name, library_configuration in self.needs['libraries'].iteritems():
                directory = os.path.join(self.needs_directory, name)
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
            print 'Building universal binary for %s' % universal_binary
    
            if not 'universal-binaries' in self.needs:
                raise ValueError('no universal binaries defined')
    
            if not universal_binary in self.needs['universal-binaries']:
                raise ValueError('unknown universal binary')
    
            if not 'libraries' in self.needs:
                return
    
            configuration = self.needs['universal-binaries'][universal_binary]
    
            for name, library_configuration in self.needs['libraries'].iteritems():
                directory = os.path.join(self.needs_directory, name)
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
        if not extension in ['.a', '.so', '.dylib']:
            return False

        subprocess.check_call(['lipo', '-create'] + inputs + ['-output', output])
        return True
