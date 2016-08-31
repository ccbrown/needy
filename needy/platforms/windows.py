import os
import platform
import subprocess

from ..filesystem import TempDir
from ..platform import Platform


class WindowsPlatform(Platform):
    @staticmethod
    def identifier():
        return 'windows'

    @staticmethod
    def is_host():
        return True

    def default_architecture(self):
        return platform.machine().lower()

    def environment_overrides(self, architecture):
        ''' visual studio comes with a batch script that set up the environments. we go to great lengths to figure out exactly what it sets... '''
        options = [architecture, 'x86_'+architecture, 'amd64_'+architecture]
        configuration = next(option for option in options if os.path.exists(os.path.join(self.__vc_root(), 'bin', option)))
        with TempDir() as d:
            path = os.path.join(d, 'script.cmd')
            with open(path, 'wb') as f:
                f.write('\r\n'.join([
                    '@set',
                    '@echo !!!',
                    '@call "{}" {}'.format(os.path.join(self.__vc_root(), 'vcvarsall.bat'), configuration),
                    '@set',
                ]).encode())
            lines = subprocess.check_output(['cmd', '/c', 'call', path]).decode().splitlines()
        before = {}
        overrides = {}
        is_after = False
        for line in lines:
            if line == '!!!':
                is_after = True
                continue
            name = str(line.split('=', 1)[0])
            value = str(line.split('=', 1)[1])
            if is_after:
                if name not in before or before[name] != value:
                    overrides[name] = value
            else:
                before[name] = value
        return overrides

    def binary_paths(self, architecture):
        return [os.path.join(self.__vc_root(), 'bin')]

    def c_compiler(self, architecture):
        return [os.path.join(self.__vc_root(), 'bin', 'cl')]

    def cxx_compiler(self, architecture):
        return self.c_compiler(architecture)

    def __vc_root(self):
        tools_path = None

        for v in range(8, 100):
            if 'VS{}0COMNTOOLS'.format(v) in os.environ:
                tools_path = os.environ['VS{}0COMNTOOLS'.format(v)].rstrip(os.path.sep)

        if tools_path is None:
            raise RuntimeError('no visual studio installation found')

        return os.path.join(os.path.dirname(os.path.dirname(tools_path)), 'VC')
