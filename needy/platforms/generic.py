from ..platform import Platform

from distutils import spawn
import platform
import os


class GenericPlatform(Platform):
    @staticmethod
    def identifier():
        return 'generic'

    @staticmethod
    def is_host():
        return True

    def default_architecture(self):
        return platform.machine()

    def c_compiler(self, architecture):
        command = 'gcc'
        if 'CC' in os.environ:
            command = os.environ['CC']
        elif spawn.find_executable('clang'):
            command = 'clang'
        if platform.system() == 'Darwin':
            return '%s -arch %s' % (command, architecture)
        return '%s -m%s' % (command, '32' if architecture == 'i386' else '64')

    def cxx_compiler(self, architecture):
        command = 'g++'
        if 'CXX' in os.environ:
            command = os.environ['CXX']
        elif spawn.find_executable('clang++'):
            command = 'clang++'
        if platform.system() == 'Darwin':
            return '%s -arch %s' % (command, architecture)
        return '%s -m%s' % (command, '32' if architecture == 'i386' else '64')
