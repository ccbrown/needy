import os
import shlex
import shutil
import subprocess

from operator import itemgetter

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
from .projects.make import MakeProject
from .projects.source import SourceProject
from .projects.xcode import XcodeProject


class Library:
    def __init__(self, configuration, directory, needy):

        self.configuration = configuration
        self.directory = directory

        if 'download' in self.configuration:
            self.source = Download(self.configuration['download'], self.configuration['checksum'], self.source_directory(), os.path.join(directory, 'download'))
        elif 'repository' in self.configuration:
            self.source = GitRepository(self.configuration['repository'], self.configuration['commit'], self.source_directory())
        elif 'directory' in self.configuration:
            self.source = Directory(self.configuration['directory'] if os.path.isabs(self.configuration['directory']) else os.path.join(os.path.dirname(needy.path()), self.configuration['directory']), self.source_directory())
        else:
            raise ValueError('no source specified in configuration')

        self.needy = needy

    def should_build(self, target):
        if 'project' not in self.configuration:
            return True

        configuration = evaluate_conditionals(self.configuration['project'], target)
        return 'build' not in configuration or configuration['build']

    def build(self, target):
        if not self.should_build(target):
            return False

        print('Building for %s %s' % (target.platform.identifier(), target.architecture))

        self.source.clean()

        configuration = evaluate_conditionals(self.configuration['project'] if 'project' in self.configuration else dict(), target)
        
        if os.path.isfile(os.path.join(self.source_directory(), 'CMakeLists.txt')):
            with cd(self.source_directory()):
                subprocess.check_call(['cmake', '-DCMAKE_INSTALL_PREFIX=%s' % self.build_directory(target), '.'])
        
        project = self.project(target, configuration)

        if not project:
            raise RuntimeError('unknown project type')

        post_clean_commands = configuration['post-clean'] if 'post-clean' in configuration else []
        with cd(project.directory()):
            for command in post_clean_commands:
                subprocess.check_call(shlex.split(command))

        build_directory = self.build_directory(target)

        if not os.path.exists(build_directory):
            os.makedirs(build_directory)

        with cd(project.directory()):
            try:
                project.configure(build_directory)
                project.pre_build(build_directory)
                project.build(build_directory)
                project.post_build(build_directory)
            except:
                shutil.rmtree(build_directory)
                raise

        return True

    def build_universal_binary(self, name, configuration):
        for platform, architectures in configuration.iteritems():
            for architecture in architectures:
                target = Target.Target(self.needy.platform(platform), architecture)
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
                target = Target.Target(self.needy.platform(platform), architecture)
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
                    subprocess.check_call(['lipo', '-create'] + builds + ['-output', os.path.join(universal_lib_directory, file)])
        except:
            shutil.rmtree(universal_binary_directory)
            raise

    def has_up_to_date_build(self, target):
        # TODO: return out-of-date if our configuration changes
        return not self.should_build(target) or os.path.exists(self.build_directory(target))

    def has_up_to_date_universal_binary(self, name, configuration):
        # TODO: return out-of-date if our configuration changes
        return os.path.exists(self.universal_binary_directory(name))

    def build_directory(self, target):
        return os.path.join(self.directory, 'build', target.platform.identifier(), target.architecture)

    def source_directory(self):
        return os.path.join(self.directory, 'source')

    def universal_binary_directory(self, name):
        return os.path.join(self.directory, 'build', 'universal', name)

    def include_path(self, target):
        return os.path.join(self.build_directory(target), 'include')

    def library_path(self, target):
        return os.path.join(self.build_directory(target), 'lib')

    def project(self, target, configuration):
        candidates = [AndroidMkProject, AutotoolsProject, BoostBuildProject, MakeProject, XcodeProject, SourceProject]

        if configuration:
            configuration = evaluate_conditionals(configuration, target)

        scores = [(len(configuration.viewkeys() & c.configuration_keys()), c) for c in candidates]
        candidates = [candidate for score, candidate in sorted(scores, key=itemgetter(0), reverse=True)]

        definition = ProjectDefinition(target, self.source_directory(), configuration)

        with cd(definition.directory):
            for candidate in candidates:
                if candidate.is_valid_project(definition):
                    return candidate(definition, self.needy)

        raise RuntimeError('unknown project type')
