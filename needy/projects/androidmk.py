import os
import shutil
import subprocess

from .. import project


class AndroidMkProject(project.Project):

    @staticmethod
    def is_valid_project(definition):
        if definition.target.platform.identifier() not in ['android']:
            return False
        if not os.path.exists(os.path.join(definition.directory, 'Android.mk')):
            return False
        return True

    def build(self, output_directory):
        if self.target().architecture == 'armv7':
            abi = 'armeabi-v7a'
        elif self.target().architecture == 'arm':
            abi = 'armeabi'
        else:
            raise ValueError('unsupported architecture')

        ndk_build_args = [
            'NDK_PROJECT_PATH=.',
            'APP_BUILD_SCRIPT=./Android.mk',
            'NDK_LIBS_OUT=%s' % os.path.join(output_directory, 'lib-temp'),
            'NDK_TOOLCHAIN=%s' % self.target().platform.toolchain(self.target().architecture),
            'APP_PLATFORM=android-%s' % self.target().platform.api_level,
            'APP_ABI=%s' % abi
        ]

        subprocess.check_call(['ndk-build'] + ndk_build_args)
        shutil.move(os.path.join(output_directory, 'lib-temp', abi), os.path.join(output_directory, 'lib'))
        shutil.rmtree(os.path.join(output_directory, 'lib-temp'))
