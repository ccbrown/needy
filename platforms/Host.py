from Platform import Platform

import os

class HostPlatform(Platform):
    @staticmethod
    def identifier():
        return 'host'

    def __command_exists(self, command):    
        try:
            subprocess.check_output([command, '--help'])
            return True
        except CalledProcessError:
            return False

    def c_compiler(self, architecture):
        command = 'gcc'
        if 'CC' in os.environ:
            command = os.environ['CC']
        elif self.__command_exists('clang'):
            command = 'clang'
        return '%s -arch=%s' % (command, architecture)

    def cxx_compiler(self, architecture):
        command = 'g++'
        if 'CXX' in os.environ:
            command = os.environ['CXX']
        elif self.__command_exists('clang++'):
            command = 'clang++'
        return '%s -arch=%s' % (command, architecture)
