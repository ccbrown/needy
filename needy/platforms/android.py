from ..platform import Platform

import os
import subprocess


class AndroidPlatform(Platform):
    def __init__(self, parameters={}):
        Platform.__init__(self, parameters)
        self.api_level = parameters.android_api_level if 'android_api_level' in parameters else None
        self.__toolchain = parameters.android_toolchain if 'android_toolchain' in parameters else None
        self.__runtime = parameters.android_runtime if 'android_runtime' in parameters else None

    @staticmethod
    def identifier():
        return 'android'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--android-api-level', default=None, help='the android API level to build for. this overrides the toolchain\'s sysroot')
        parser.add_argument('--android-toolchain', default=None, help='the android toolchain to build with')
        parser.add_argument('--android-runtime', default='libstdc++', choices=['libstdc++', 'gnustl_shared'], help='the android runtime to use')

    def toolchain_path(self, architecture):
        if self.__toolchain:
            return self.__toolchain

        try:
            which = subprocess.check_output(['which', '{}-c++'.format(self.binary_prefix(architecture))])
            return os.path.dirname(os.path.dirname(which))
        except subprocess.CalledProcessError:
            pass

        toolchain = None
        if 'arm' in architecture:
            toolchain = 'arm-linux-androideabi-4.9'
        else:
            raise ValueError('unsupported architecture')

        path = os.path.join(self.ndk_home(), 'toolchains', toolchain, 'prebuilt')
        if not os.path.exists(path):
            raise ValueError('missing toolchain: {}'.format(path))

        prebuilts = os.listdir(path)
        if len(prebuilts) > 0:
            return os.path.join(path, prebuilts[0])

        raise ValueError('missing toolchain: {}'.format(path))

    def sysroot_path(self, architecture):
        if self.api_level is None:
            return os.path.join(self.toolchain_path(architecture), 'sysroot')

        arch_directory = None

        if architecture == 'arm64':
            arch_directory = 'arch-arm64'
        elif 'arm' in architecture:
            arch_directory = 'arch-arm'
        else:
            raise ValueError('unsupported architecture')

        return os.path.join(self.ndk_home(), 'platforms', 'android-%s' % self.api_level, arch_directory)

    def __cxx_stl_architecture_name(self, architecture):
        if architecture == 'armv7':
            return 'armeabi-v7a'
        raise ValueError('unsupported architecture')

    def binary_prefix(self, architecture):
        if 'arm' in architecture:
            return 'arm-linux-androideabi'
        raise ValueError('unsupported architecture')

    def binary_paths(self, architecture):
        toolchain_path = self.toolchain_path(architecture)
        return [os.path.join(toolchain_path, self.binary_prefix(architecture), 'bin'), os.path.join(toolchain_path, 'bin')]

    def __gnustl_path(self):
        return os.path.join(self.ndk_home(), 'sources', 'cxx-stl', 'gnu-libstdc++', '4.9')

    def __gunstl_lib_path(self, architecture):
        return os.path.join(self.__gnustl_path(), 'libs', self.__cxx_stl_architecture_name(architecture))

    def include_paths(self, architecture):
        ret = []

        if self.__runtime == 'gnustl_shared':
            ret.extend([
                os.path.join(self.__gnustl_path(), 'include'),
                os.path.join(self.__gnustl_path(), 'include', 'backward'),
                os.path.join(self.__gunstl_lib_path(architecture), 'include')
            ])

        return ret

    def libraries(self, architecture):
        if self.__runtime == 'gnustl_shared':
            return [
                os.path.join(self.__gnustl_path(), 'libgnustl_shared.so'),
                os.path.join(self.__gunstl_lib_path(architecture), 'libsupc++.a')
            ]
        else:
            return ['-lstdc++', '-lm']

    def __compiler_args(self, architecture):
        ret = []

        if self.api_level:
            ret.append('--sysroot=%s' % self.sysroot_path(architecture))

        if 'arm' in architecture:
            if architecture == 'armv7':
                ret.append('-march=armv7-a')
            else:
                ret.append('-march=%s' % architecture)

        include_paths = self.include_paths(architecture)
        for path in include_paths:
            ret.append('-I%s' % path)

        return ' '.join(ret)

    def c_compiler(self, architecture):
        return self.__compiler(architecture, ['clang', 'gcc'])

    def cxx_compiler(self, architecture):
        return self.__compiler(architecture, ['clang++', 'g++'])

    def __compiler(self, architecture, choices):
        prefix = self.binary_prefix(architecture)
        for compiler in ['{}-{}'.format(prefix, c) for c in choices]:
            if os.path.exists(os.path.join(self.toolchain_path(architecture), 'bin', compiler)):
                return '{} {}'.format(compiler, self.__compiler_args(architecture))
        raise RuntimeError('Unable to locate a suitable compiler matching {} in {}'.format(choices, os.path.join(self.toolchain_path(architecture), 'bin')))

    def ndk_home(self):
        ndk_home = os.getenv('ANDROID_NDK_HOME', os.getenv('NDK_HOME'))
        if not ndk_home:
            raise RuntimeError('unable to locate ndk')
        return ndk_home

    def default_architecture(self):
        return 'armv7'
