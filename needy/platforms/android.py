import os
import subprocess
import pipes
import logging

from ..platform import Platform
from ..memoize import MemoizeMethod


class AndroidPlatform(Platform):
    def __init__(self, parameters={}):
        Platform.__init__(self, parameters)
        self.api_level = parameters.android_api_level if 'android_api_level' in parameters else None
        self.__toolchain = parameters.android_toolchain if 'android_toolchain' in parameters else None
        self.__runtime = parameters.android_runtime

    @staticmethod
    def identifier():
        return 'android'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--android-api-level',
                            default=None,
                            help='the android API level to build for. this overrides the toolchain\'s sysroot')
        parser.add_argument('--android-toolchain',
                            default=None,
                            help='the android toolchain to build with')
        parser.add_argument('--android-runtime',
                            default='c++_static',
                            choices=['c++_shared', 'c++_static'],
                            help='the android runtime to use')

    def toolchain_path(self, architecture):
        if self.__toolchain:
            return self.__toolchain

        if 'ANDROID_TOOLCHAIN' in os.environ:
            return os.environ['ANDROID_TOOLCHAIN']

        try:
            which = subprocess.check_output(['which', '{}-c++'.format(self.binary_prefix(architecture))])
            return os.path.dirname(os.path.dirname(which))
        except subprocess.CalledProcessError:
            pass

        toolchain = None
        if 'arm' in architecture:
            toolchain = 'arm-linux-androideabi-4.9'
        else:
            raise ValueError('unsupported architecture: {}'.format(architecture))

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
            raise ValueError('unsupported architecture: {}'.format(architecture))

        return os.path.join(self.ndk_home(), 'platforms', 'android-{}'.format(self.api_level), arch_directory)

    def binary_prefix(self, architecture):
        if 'arm' in architecture:
            return 'arm-linux-androideabi'
        raise ValueError('unsupported architecture: {}'.format(architecture))

    def binary_paths(self, architecture):
        toolchain_path = self.toolchain_path(architecture)
        return [
            os.path.join(toolchain_path, self.binary_prefix(architecture), 'bin'),
            os.path.join(toolchain_path, 'bin')
        ]

    def __compiler_args(self, architecture):
        ret = []

        if self.api_level:
            ret.append('--sysroot=%s' % self.sysroot_path(architecture))

        if 'arm' in architecture:
            if architecture == 'armv7':
                ret.append('-march=armv7-a')
            else:
                ret.append('-march={}'.format(architecture))

        return ret

    def c_compiler(self, architecture):
        return self.__compiler(architecture, ['clang'])

    def cxx_compiler(self, architecture):
        return self.__compiler(architecture, ['clang++'])

    def __compiler(self, architecture, choices):
        prefix = self.binary_prefix(architecture)
        for compiler in ['{}-{}'.format(prefix, c) for c in choices]:
            for path in self.binary_paths(architecture):
                if os.path.exists(os.path.join(path, compiler)):
                    return [compiler] + self.__compiler_args(architecture)
        raise RuntimeError('Unable to locate a suitable compiler matching {} in {}'.format(choices, os.path.join(self.toolchain_path(architecture), 'bin')))

    def ndk_home(self):
        ndk_home = os.getenv('ANDROID_NDK_HOME', os.getenv('NDK_HOME'))
        if not ndk_home:
            raise RuntimeError('unable to locate ndk in ANDROID_NDK_HOME or NDK_HOME')
        return ndk_home

    def default_architecture(self):
        return 'armv7'

    def configuration(self, architecture):
        api_level = 0
        compiler = self.cxx_compiler(architecture)
        binary_paths = self.binary_paths(architecture)
        d = Platform.configuration(self, architecture)
        d.update({
            'api-level': self.__android_api_level(compiler, binary_paths),
            'runtime': self.__runtime,
            'runtime-version': {
                'libc++-version': self.__libcpp_version(compiler, binary_paths),
                'libc++-abi-version': self.__libcpp_abi_version(compiler, binary_paths)
            }
        })
        return d

    @classmethod
    @MemoizeMethod
    def __android_api_level(cls, compiler, binary_paths):
        try:
            out = cls.__compiler_preprocessing_output(
                compiler=compiler,
                binary_paths=binary_paths,
                program='#include <android/api-level.h>\n__ANDROID_API__'
            )
            return int(out[-1])
        except (ValueError, CalledProcessError):
            logging.warning('unable to determine android api level')

    @classmethod
    @MemoizeMethod
    def __libcpp_version(cls, compiler, binary_paths):
        out = cls.__compiler_preprocessing_output(
            compiler=compiler,
            binary_paths=binary_paths,
            program='#include <string>\n_LIBCPP_VERSION'
        )
        if out and out[-1]:
            return out[-1]
        else:
            logging.warning('unable to determine libc++ version')

    @classmethod
    @MemoizeMethod
    def __libcpp_abi_version(cls, compiler, binary_paths):
        out = cls.__compiler_preprocessing_output(
            compiler=compiler,
            binary_paths=binary_paths,
            program='#include <string>\n_LIBCPP_ABI_VERSION'
        )
        if out and out[-1]:
            return out[-1]
        else:
            logging.warning('unable to determine libc++ abi version')

    @classmethod
    def __compiler_preprocessing_output(cls, compiler, binary_paths, program):
        # The compiler for android is implemented as a shell script (without the
        # shebang line, grrr) so we have to use sh to interpret it AND have to
        # be sure to use a full path because otherwise the shell script fails
        # AND it appears that invocations from Popen in the portable manner seem
        # to hang as if waiting on stdin despite closing the fd via communicate.
        try:
            env = os.environ.copy()
            env['PATH'] = '{}:{}'.format(':'.join(binary_paths), env['PATH'])
            cmd = 'printf \'{}\' | {} -x c++ -P -E -'.format(program, ' '.join([pipes.quote(c) for c in compiler]))
            return subprocess.check_output(cmd, env=env, shell=True).decode().strip().split('\n')
        except subprocess.CalledProcessError:
            pass
