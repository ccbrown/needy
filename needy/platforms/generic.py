from ..platform import Platform

import platform
import os
import subprocess


class GenericPlatform(Platform):
    @staticmethod
    def identifier():
        return 'generic'

    @staticmethod
    def is_host():
        return True

    def __command_exists(self, command):
        try:
            subprocess.check_output([command, '--help'])
            return True
        except subprocess.CalledProcessError:
            return False

    def default_architecture(self):
        return platform.machine()

    def c_compiler(self, architecture):
        command = 'gcc'
        if 'CC' in os.environ:
            command = os.environ['CC']
        elif self.__command_exists('clang'):
            command = 'clang'
        return '%s -arch %s' % (command, architecture)

    def cxx_compiler(self, architecture):
        command = 'g++'
        if 'CXX' in os.environ:
            command = os.environ['CXX']
        elif self.__command_exists('clang++'):
            command = 'clang++'
        return '%s -arch %s' % (command, architecture)
