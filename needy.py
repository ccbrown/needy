#!/usr/bin/env python

import os, subprocess

from platforms import Host
from platforms import IOS
from platforms import Android

class Needy:
    def __init__(self, path, parameters):
        import json

        self.path = path
        self.parameters = parameters

        with open(self.path, 'r') as needs_file:
            self.needs = json.load(needs_file)

        self.needs_directory = self.determine_needs_directory()
    
    def platform(self, identifier):
        if identifier is 'host':
            return Host.HostPlatform()
        if identifier is 'ios':
            return IOS.IOSPlatform()
        if identifier is 'android':
            return Android.AndroidPlatform(self.parameters.android_api_level)
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

        from libraries import Library

        print 'Building libraries for %s' % target.platform.identifier()
        if target.architecture:
            print 'Architecture: %s' % target.architecture

        for name, library_configuration in self.needs['libraries'].iteritems():
            directory = os.path.join(self.needs_directory, name)
            library = Library.Library(library_configuration, directory, self)
            if library.has_up_to_date_build(target):
                print '[UP-TO-DATE] %s' % name
            else:
                print '[LIBRARY] %s' % name
                library.build(target)
                print '[SUCCESS]'

    def satisfy_universal_binary(self, universal_binary):
        from libraries import Library, Target

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
            library = Library.Library(library_configuration, directory, self)
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

def main(args):
    import argparse

    parser = argparse.ArgumentParser(description='Satisfies needs.')
    parser.add_argument('--target', help='builds needs for this target (example: iphone:armv7)')
    parser.add_argument('--universal-binary', help='builds the universal binary with the given name')
    parser.add_argument('--android-api-level', default='21', help='the android API level to build for')
    parameters = parser.parse_args(args[1:])

    needy = Needy(os.path.abspath('needs.json'), parameters)

    print 'Satisfying needs for: %s' % needy.path
    print 'Needs directory: %s' % needy.needs_directory

    if parameters.target or parameters.universal_binary == None:
        from libraries import Target
        if parameters.target:
            parts = parameters.target.split(':')
            platform = needy.platform(parts[0])
            target = Target.Target(platform, parts[1] if len(parts) > 1 else platform.default_architecture())
        else:
            target = Target.Target(Host.HostPlatform())
        needy.satisfy_target(target)

    if parameters.universal_binary:
        needy.satisfy_universal_binary(parameters.universal_binary)

if __name__ == "__main__":
    import sys

    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print '[ERROR]', e
        raise
