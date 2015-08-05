#!/usr/bin/env python

import json
import os
import subprocess
import sys

from library import Library
from target import Target

from platforms.host import HostPlatform
from platforms.ios import IOSPlatform
from platforms.android import AndroidPlatform

class Needy:
    def __init__(self, path, parameters):
        self.path = path
        self.parameters = parameters

        with open(self.path, 'r') as needs_file:
            self.needs = json.load(needs_file)

        self.needs_directory = self.determine_needs_directory()
    
    def platform(self, identifier):
        if identifier == 'host':
            return HostPlatform()
        if identifier == 'ios':
            return IOSPlatform(self.parameters.minimum_ios_version)
        if identifier == 'android':
            return AndroidPlatform(self.parameters.android_api_level)
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

        print 'Building libraries for %s %s' % (target.platform.identifier(), target.architecture)

        for name, library_configuration in self.needs['libraries'].iteritems():
            directory = os.path.join(self.needs_directory, name)
            library = Library(library_configuration, directory, self)
            if library.has_up_to_date_build(target):
                print '[UP-TO-DATE] %s' % name
            else:
                print '[LIBRARY] %s' % name
                library.build(target)
                print '[SUCCESS]'

    def satisfy_universal_binary(self, universal_binary):
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
                print '[UP-TO-DATE] %s' % name
            else:
                print '[LIBRARY] %s' % name
                library.build_universal_binary(universal_binary, configuration)
                print '[SUCCESS]'

    def create_universal_binary(self, inputs, output):
        name, extension = os.path.splitext(output)
        if not extension in ['.a', '.so', '.dylib']:
            return False

        subprocess.check_call(['lipo', '-create'] + inputs + ['-output', output])
        return True

    def determine_needs_directory(self):
        directory = os.path.dirname(self.path)
        needy_directory = directory

        while directory != '/':
            directory = os.path.dirname(directory)
            if os.path.isfile(os.path.join(directory, 'needs.json')):
                needy_directory = directory

        return os.path.join(needy_directory, 'needs')
