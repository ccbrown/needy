import os
import shutil

from .. import project


class AndroidMkProject(project.Project):

    @staticmethod
    def identifier():
        return 'androidmk'

    @staticmethod
    def is_valid_project(definition, needy):
        if definition.target.platform.identifier() not in ['android']:
            return False, 'platform identifier is not android'
        if not os.path.exists(os.path.join(definition.directory, 'Android.mk')):
            return False, 'Android.mk not found'
        return True, 'Android.mk found'

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

        self.command([os.path.join(self.target().platform.ndk_home(), 'ndk-build')] + ndk_build_args)
        shutil.move(os.path.join(output_directory, 'lib-temp', abi), os.path.join(output_directory, 'lib'))
        shutil.rmtree(os.path.join(output_directory, 'lib-temp'))
