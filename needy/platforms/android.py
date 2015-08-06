from ..platform import Platform

import os

class AndroidPlatform(Platform):
    def __init__(self, parameters):
        Platform.__init__(self, parameters)
        self.api_level = parameters.android_api_level
    
    @staticmethod
    def identifier():
        return 'android'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--android-api-level', default='21', help='the android API level to build for')

    def toolchain(self, architecture):
        if architecture.find('arm') >= 0:
            return 'arm-linux-androideabi-4.9'
        else:
            raise ValueError('unsupported architecture')

    def toolchain_path(self, architecture):
        path = os.path.join(self.ndk_home(), 'toolchains', self.toolchain(architecture), 'prebuilt', 'darwin-x86_64')
        if not os.path.exists(path):
            raise ValueError('missing toolchain: %s' % path)
        return path

    def sysroot_path(self, architecture):
        arch_directory = None

        if architecture == 'arm64':
            arch_directory = 'arch-arm64'
        elif architecture.find('arm') >= 0:
            arch_directory = 'arch-arm'
        else:
            raise ValueError('unsupported architecture')

        return os.path.join(self.ndk_home(), 'platforms', 'android-%s' % self.api_level, arch_directory)

    def __cxx_stl_architecture_name(self, architecture):
        if architecture == 'armv7':
            return 'armeabi-v7a'
        raise ValueError('unsupported architecture')

    def binary_prefix(self, architecture):
        if architecture.find('arm') >= 0:
            return 'arm-linux-androideabi'
        raise ValueError('unsupported architecture')

    def binary_paths(self, architecture):
        toolchain_path = self.toolchain_path(architecture)        
        return [os.path.join(toolchain_path, self.binary_prefix(architecture), 'bin'), os.path.join(toolchain_path, 'bin')]

    def include_paths(self, architecture):
        ret = [
            self.sysroot_path(architecture),
            os.path.join(self.ndk_home(), 'sources', 'cxx-stl', 'gnu-libstdc++', '4.9', 'include'),
            os.path.join(self.ndk_home(), 'sources', 'cxx-stl', 'gnu-libstdc++', '4.9', 'include', 'backward'),
            os.path.join(self.ndk_home(), 'sources', 'cxx-stl', 'gnu-libstdc++', '4.9', 'libs', self.__cxx_stl_architecture_name(architecture), 'include')
        ]

        return ret
        
    def libraries(self, architecture):
        return [
            os.path.join(self.ndk_home(), 'sources', 'cxx-stl', 'gnu-libstdc++', '4.9', 'libs', self.__cxx_stl_architecture_name(architecture), 'libgnustl_shared.so'),
            os.path.join(self.ndk_home(), 'sources', 'cxx-stl', 'gnu-libstdc++', '4.9', 'libs', self.__cxx_stl_architecture_name(architecture), 'libsupc++.a')
        ]

    def __compiler_args(self, architecture):
        ret = ['--sysroot=%s' % self.sysroot_path(architecture)]

        if architecture.find('arm') >= 0:
            ret.append('-mthumb')
            ret.append('-march=%s' % architecture)

        include_paths = self.include_paths(architecture)
        for path in include_paths:
            ret.append('-I%s' % path)

        return ret

    def c_compiler(self, architecture):
        return 'arm-linux-androideabi-gcc %s' % ' '.join(self.__compiler_args(architecture))

    def cxx_compiler(self, architecture):
        return 'arm-linux-androideabi-g++ %s' % ' '.join(self.__compiler_args(architecture))

    def ndk_home(self):
        ndk_home = os.getenv('ANDROID_NDK_HOME', os.getenv('NDK_HOME'))
        if not ndk_home:
            raise RuntimeError('unable to locate ndk')
        return ndk_home
