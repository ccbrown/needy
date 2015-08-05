from .. import Project
import os
import subprocess
import shutil

from ..ChangeDir import cd


class XcodeProject(Project.Project):

    @staticmethod
    def is_valid_project(definition):
        if definition.target.platform.identifier() not in ['host', 'ios']:
            return False

        xcodebuild_args = []

        if 'xcode-project' in definition.configuration:
            xcodebuild_args.extend(['-project', definition.configuration['xcode-project']])

        try:
            with cd(definition.directory):
                with open(os.devnull, 'w') as devnull:
                    subprocess.check_call(['xcodebuild', '-list'] + xcodebuild_args, stdout=devnull)
        except:
            return False
        return True

    def build(self, output_directory):
        xcodebuild_args = ['-parallelizeTargets', 'ONLY_ACTIVE_ARCH=YES', 'USE_HEADER_SYMLINKS=YES']

        if self.configuration('xcode-project'):
            xcodebuild_args.extend(['-project', self.configuration('xcode-project')])

        if self.target().platform.identifier() == 'ios':
            xcodebuild_args.extend(['-sdk', 'iphoneos'])

        if self.target().architecture:
            xcodebuild_args.extend(['-arch', self.target().architecture])

        extras_build_dir = os.path.join(output_directory, 'extras')

        subprocess.check_call(['xcodebuild'] + xcodebuild_args + [
            'INSTALL_PATH=%s' % extras_build_dir,
            'INSTALL_ROOT=/',
            'SKIP_INSTALL=NO',
            'PUBLIC_HEADERS_FOLDER_PATH=%s' % os.path.join(output_directory, 'include'),
            'PRIVATE_HEADERS_FOLDER_PATH=%s' % os.path.join(output_directory, 'include'),
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
