import binascii
import hashlib
import json
import os
import shlex
import shutil

from operator import itemgetter

try:
    from colorama import Fore
except ImportError:
    class EmptyStringAttributes:
        def __getattr__(self, name):
            return ''
    Fore = EmptyStringAttributes()

from .project import evaluate_conditionals
from .project import ProjectDefinition

from .sources.download import Download
from .sources.directory import Directory
from .sources.git import GitRepository

from .cd import cd
from .target import Target

from .projects.androidmk import AndroidMkProject
from .projects.autotools import AutotoolsProject
from .projects.boostbuild import BoostBuildProject
from .projects.cmake import CMakeProject
from .projects.custom import CustomProject
from .projects.make import MakeProject
from .projects.source import SourceProject
from .projects.xcode import XcodeProject


class Library:
    def __init__(self, configuration, directory, needy):

        self.__configuration = configuration
        self.__directory = directory

        if 'download' in self.__configuration:
            self.source = Download(self.__configuration['download'], self.__configuration['checksum'], self.source_directory(), os.path.join(directory, 'download'))
        elif 'repository' in self.__configuration:
            self.source = GitRepository(self.__configuration['repository'], self.__configuration['commit'], self.source_directory())
        elif 'directory' in self.__configuration:
            self.source = Directory(self.__configuration['directory'] if os.path.isabs(self.__configuration['directory']) else os.path.join(os.path.dirname(needy.path()), self.__configuration['directory']), self.source_directory())
        else:
            raise ValueError('no source specified in configuration')

        self.needy = needy

    def configuration(self, target):
        return evaluate_conditionals(self.__configuration['project'] if 'project' in self.__configuration else dict(), target)

    def should_build(self, target):
        configuration = self.configuration(target)
        return 'build' not in configuration or configuration['build']

    def build(self, target):
        if not self.should_build(target):
            return False

        print('Building for %s %s' % (target.platform.identifier(), target.architecture))

        if ' ' in self.__directory:
            print(Fore.YELLOW + '[WARNING]' + Fore.RESET + ' The build path contains spaces. Some build systems don\'t handle spaces well, so if you have problems, consider moving the project or using a symlink.')

        self.source.clean()

        configuration = self.configuration(target)
        
        post_clean_commands = configuration['post-clean'] if 'post-clean' in configuration else []
        with cd(self.source_directory()):
            if isinstance(post_clean_commands, list):
                for command in post_clean_commands:
                    self.needy.command(shlex.split(command))
            else:
                self.needy.command(shlex.split(post_clean_commands))

        definition = ProjectDefinition(target, self.source_directory(), configuration)
        project = self.project(definition)

        if not project:
            raise RuntimeError('unknown project type')

        build_directory = self.build_directory(target)

        if os.path.exists(build_directory):
            shutil.rmtree(build_directory)

        os.makedirs(build_directory)
        
        with cd(self.source_directory()):
            try:
                project.configure(build_directory)
                project.pre_build(build_directory)
                project.build(build_directory)
                project.post_build(build_directory)
            except:
                shutil.rmtree(build_directory)
                raise

        with open(self.build_status_path(target), 'w') as status_file:
            status = {
                'configuration': binascii.hexlify(self.__configuration_hash(target))
            }
            json.dump(status, status_file)

        return True

    def build_universal_binary(self, name, configuration):
        for platform, architectures in configuration.iteritems():
            for architecture in architectures:
                target = Target(self.needy.platform(platform), architecture)
                if not self.has_up_to_date_build(target):
                    if not self.build(target):
                        print('Skipping universal binary %s' % name)
                        return

        print('Building universal binary %s' % name)

        files = dict()
        target_count = 0

        for platform, architectures in configuration.iteritems():
            for architecture in architectures:
                target_count = target_count + 1
                target = Target(self.needy.platform(platform), architecture)
                lib_directory = os.path.join(self.build_directory(target), 'lib')
                for file in os.listdir(lib_directory):
                    if not os.path.isfile(os.path.join(lib_directory, file)):
                        continue
                    if file not in files:
                        files[file] = []
                    files[file].append(os.path.join(lib_directory, file))

        universal_binary_directory = self.universal_binary_directory(name)

        if os.path.exists(universal_binary_directory):
            shutil.rmtree(universal_binary_directory)

        universal_lib_directory = os.path.join(self.universal_binary_directory(name), 'lib')
        os.makedirs(universal_lib_directory)

        try:
            for file, builds in files.iteritems():
                if len(builds) != target_count:
                    continue

                file_name, extension = os.path.splitext(file)

                if extension in ['.a', '.dylib', '.so']:
                    print('Creating universal library %s' % file)
                    self.needy.command(['lipo', '-create'] + builds + ['-output', os.path.join(universal_lib_directory, file)])
        except:
            shutil.rmtree(universal_binary_directory)
            raise

    def has_up_to_date_build(self, target):
        if not self.should_build(target):
            return True

        if not os.path.isfile(self.build_status_path(target)):
            return False
        
        configuration = self.configuration(target)
        
        try:
            with open(self.build_status_path(target), 'r') as status_file:
                status = json.load(status_file)
                if binascii.unhexlify(status['configuration']) != self.__configuration_hash(target):
                    return False
        except ValueError:
            return False

        return True

    def has_up_to_date_universal_binary(self, name, configuration):
        for platform, architectures in configuration.iteritems():
            for architecture in architectures:
                target = Target(self.needy.platform(platform), architecture)
                if self.should_build(target) and not self.has_up_to_date_build(target):
                    return False
        return os.path.exists(self.universal_binary_directory(name))

    def build_directory(self, target):
        return os.path.join(self.__directory, 'build', target.platform.identifier(), target.architecture)

    def build_status_path(self, target):
        return os.path.join(self.build_directory(target), 'needy.status')

    def source_directory(self):
        return os.path.join(self.__directory, 'source')

    def universal_binary_directory(self, name):
        return os.path.join(self.__directory, 'build', 'universal', name)

    def include_path(self, target):
        return os.path.join(self.build_directory(target), 'include')

    def library_path(self, target_or_universal_binary):
        return os.path.join(self.build_directory(target_or_universal_binary) if isinstance(target_or_universal_binary, Target) else self.universal_binary_directory(target_or_universal_binary), 'lib')

    def project(self, definition):
        candidates = [AndroidMkProject, AutotoolsProject, CMakeProject, BoostBuildProject, MakeProject, XcodeProject, SourceProject, CustomProject]

        if 'type' in definition.configuration:
            for candidate in candidates:
                if candidate.identifier() == definition.configuration['type']:
                    return candidate(definition, self.needy)
            raise RuntimeError('unknown project type') 

        scores = [(len(definition.configuration.viewkeys() & c.configuration_keys()), c) for c in candidates]
        candidates = [candidate for score, candidate in sorted(scores, key=itemgetter(0), reverse=True)]

        with cd(definition.directory):
            for candidate in candidates:
                if candidate.is_valid_project(definition, self.needy):
                    return candidate(definition, self.needy)

        raise RuntimeError('unknown project type')

    def __configuration_hash(self, target):
        hash = hashlib.sha256()

        top = self.__configuration.copy()
        top.pop('project', None)
        hash.update(json.dumps(top, sort_keys=True))

        hash.update(json.dumps(self.configuration(target), sort_keys=True))

        return hash.digest()
