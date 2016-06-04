import os
import subprocess
import shutil
import logging

from .. import project
from ..cd import cd
from ..process import command_output
from ..platforms.xcode import XcodePlatform

from .source import SourceProject


class XcodeProject(project.Project):

    @staticmethod
    def identifier():
        return 'xcode'

    @staticmethod
    def is_valid_project(definition, needy):
        if not isinstance(definition.target.platform, XcodePlatform):
            return False, 'target platform not an Xcode supported platform'

        xcodebuild_args = []

        if 'xcode-project' in definition.configuration:
            xcodebuild_args.extend(['-project', definition.configuration['xcode-project']])

        try:
            with cd(definition.directory):
                command_output(['xcodebuild', '-list'] + xcodebuild_args, logging.DEBUG)
        except subprocess.CalledProcessError:
            return False, 'non-zero return in xcodebuild -list indicating no xcode project located in project root'
        except OSError:
            return False, 'xcodebuild could not be invoked'
        return True, 'xcodebuild -list return zero indicating valid project'

    @staticmethod
    def configuration_keys():
        return project.Project.configuration_keys() | {'xcode-project', 'xcode-scheme', 'xcode-target'}

    def target_environment_overrides(self):
        # CC and CXX will likely be correct when invoked by xcode directly
        ret = project.Project.target_environment_overrides(self)
        for var in ['CC', 'CXX']:
            if var in ret:
                del ret[var]
        return ret

    def build(self, output_directory):
        xcodebuild_args = ['-parallelizeTargets', 'ONLY_ACTIVE_ARCH=YES', 'USE_HEADER_SYMLINKS=YES']

        if self.configuration('xcode-project'):
            xcodebuild_args.extend(['-project', self.configuration('xcode-project')])
        if self.configuration('xcode-scheme'):
            xcodebuild_args.extend(['-scheme', self.configuration('xcode-scheme')])
        if self.configuration('xcode-target'):
            xcodebuild_args.extend(['-target', self.configuration('xcode-target')])

        xcodebuild_args.extend(['-sdk', self.target().platform.sdk()])

        if self.target().architecture:
            xcodebuild_args.extend(['-arch', self.target().architecture])

        extras_build_dir = os.path.join(output_directory, 'extras')
        include_directory = os.path.join(output_directory, 'include')

        self.command(['xcodebuild'] + xcodebuild_args + [
            'INSTALL_PATH=%s' % extras_build_dir,
            'INSTALL_ROOT=/',
            'SKIP_INSTALL=NO',
            'PUBLIC_HEADERS_FOLDER_PATH=%s' % include_directory,
            'PRIVATE_HEADERS_FOLDER_PATH=%s' % include_directory,
            'install', 'installhdrs'
        ])

        lib_extensions = ['.a', '.dylib', '.so', '.la']
        lib_directory = os.path.join(output_directory, 'lib')

        if not os.path.exists(lib_directory):
            os.makedirs(lib_directory)

        for file in os.listdir(extras_build_dir):
            name, extension = os.path.splitext(file)
            if extension in lib_extensions:
                shutil.move(os.path.join(extras_build_dir, file), lib_directory)

        if not os.listdir(extras_build_dir):
            os.rmdir(extras_build_dir)

        if not os.listdir(include_directory):
            SourceProject.copy_headers(self.directory(), self.configuration(), include_directory)
