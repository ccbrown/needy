import os
import shlex
import shutil
import subprocess

from project import evaluate_conditionals
from project import ProjectDefinition

from download import Download
from git import GitRepository

from cd import cd

from projects.androidmk import AndroidMkProject
from projects.autotools import AutotoolsProject
from projects.boostbuild import BoostBuildProject
from projects.make import MakeProject
from projects.source import SourceProject
from projects.xcode import XcodeProject

class Library:
    def __init__(self, configuration, directory, needy):

        self.configuration = configuration
        self.directory = directory
        self.source_directory = os.path.join(directory, 'source')

        if 'download' in self.configuration:
            self.source = Download(self.configuration['download'], self.configuration['checksum'], self.source_directory, os.path.join(directory, 'download'))
        elif 'repository' in self.configuration:
            self.source = GitRepository(self.configuration['repository'], self.configuration['commit'], self.source_directory)
        else:
            raise ValueError('no source specified in configuration')

        self.needy = needy

    def build(self, target):
        configuration = evaluate_conditionals(self.configuration['project'] if 'project' in self.configuration else dict(), target)

        if 'build' in configuration and not configuration['build']:
            print 'Skipping for %s' % target.platform.identifier()
            return False

        self.source.clean()

        project = self.project(target, configuration)

        post_clean_commands = self.configuration['post-clean'] if 'post-clean' in self.configuration else []
        with cd(project.directory()):
            for command in post_clean_commands:
                subprocess.check_call(shlex.split(command))

        print 'Building for %s %s' % (target.platform.identifier(), target.architecture)

        if not project:
            raise RuntimeError('unknown project type')

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
        import shutil, subprocess, Target

        for platform, architectures in configuration.iteritems():
            for architecture in architectures:
                target = Target.Target(self.needy.platform(platform), architecture)
                if not self.has_up_to_date_build(target):
                    if not self.build(target):
                        print 'Skipping universal binary %s' % name
                        return

        print 'Building universal binary %s' % name

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
                    if not file in files:
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
                    print 'Creating universal library %s' % file
                    subprocess.check_call(['lipo', '-create'] + builds + ['-output', os.path.join(universal_lib_directory, file)])
        except:
            shutil.rmtree(universal_binary_directory)
            raise

    def has_up_to_date_build(self, target):
        # TODO: return out-of-date if our configuration changes
        return os.path.exists(self.build_directory(target))

    def has_up_to_date_universal_binary(self, name, configuration):
        # TODO: return out-of-date if our configuration changes
        return os.path.exists(self.universal_binary_directory(name))

    def build_directory(self, target):
        return os.path.join(self.directory, 'build', target.platform.identifier(), target.architecture)

    def universal_binary_directory(self, name):
        return os.path.join(self.directory, 'build', 'universal', name)

    def project(self, target, configuration):
        candidates = [AndroidMkProject, AutotoolsProject, BoostBuildProject, MakeProject, XcodeProject]

        if configuration:
            configuration = Project.evaluate_conditionals(configuration, target)

        if 'b2-args' in configuration:
            candidates.insert(0, BoostBuildProject)

        if 'configure-args' in configuration:
            candidates.insert(0, AutotoolsProject)

        if 'xcode-project' in configuration:
            candidates.insert(0, XcodeProject)

        if 'source-directory' in configuration:
            candidates.insert(0, SourceProject)

        definition = ProjectDefinition(target, self.source_directory, configuration)

        with cd(definition.directory):
            for candidate in candidates:
                if candidate.is_valid_project(definition):
                    return candidate(definition, self.needy)

        raise RuntimeError('unknown project type')
