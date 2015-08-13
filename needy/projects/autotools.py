import os
import subprocess

from .. import project
from ..cd import cd

from .make import get_make_jobs_args


class AutotoolsProject(project.Project):

    @staticmethod
    def is_valid_project(definition):
        with cd(definition.directory):
            if os.path.isfile('configure'):
                try:
                    configure_version_info = subprocess.check_output(['./configure', '--version'])
                    if 'generated by GNU Autoconf' in configure_version_info:
                        return True
                except subprocess.CalledProcessError:
                    pass
            if os.path.isfile('autogen.sh') and os.path.isfile('configure.ac') and os.path.isfile('Makefile.am'):
                return True
        return False

    @staticmethod
    def configuration_keys():
        return ['configure-args']

    def configure(self, output_directory):
        if not os.path.isfile(os.path.join(self.directory(), 'configure')):
            subprocess.check_call('./autogen.sh')

        configure_args = self.configuration('configure-args') or []

        configure_args.append('--prefix=%s' % output_directory)

        linkage = self.configuration('linkage')

        c_compiler = self.target().platform.c_compiler(self.target().architecture)
        if c_compiler:
            configure_args.append('CC=%s' % c_compiler)

        cxx_compiler = self.target().platform.cxx_compiler(self.target().architecture)
        if cxx_compiler:
            configure_args.append('CXX=%s' % cxx_compiler)

        libraries = self.target().platform.libraries(self.target().architecture)
        if len(libraries) > 0:
            configure_args.append('LDFLAGS=%s' % ' '.join(libraries))

        binary_paths = self.target().platform.binary_paths(self.target().architecture)
        if len(binary_paths) > 0:
            configure_args.append('PATH=%s:%s' % (':'.join(binary_paths), os.environ['PATH']))

        if self.target().platform.identifier() == 'ios':
            if not linkage:
                linkage = 'static'

            configure_host = self.__available_configure_host([
                '%s-apple-darwin' % self.target().architecture, 'arm*-apple-darwin', 'arm-apple-darwin', 'arm*', 'arm'
            ])

            if configure_host == 'arm*-apple-darwin':
                configure_host = '%s-apple-darwin' % self.target().architecture
            elif configure_host == 'arm*':
                configure_host = self.target().architecture
            elif not configure_host:
                configure_host = 'arm-apple-darwin'

            configure_args.append('--host=%s' % configure_host)
        elif self.target().platform.identifier() == 'android':
            toolchain = self.target().platform.toolchain_path(self.target().architecture)
            sysroot = self.target().platform.sysroot_path(self.target().architecture)

            if self.target().architecture.find('arm') >= 0:
                configure_host = self.__available_configure_host([
                    'linux*android*', 'arm*', 'arm'
                ])

                if configure_host == 'linux*android*':
                    configure_host = 'arm-linux-androideabi'
                elif configure_host == 'arm*':
                    configure_host = self.target().architecture
                elif not configure_host:
                    configure_host = 'arm-linux-androideabi'

                configure_args.extend([
                    'CFLAGS=-mthumb -march=%s' % self.target().architecture
                ])

            configure_args.extend([
                '--host=%s' % configure_host,
                '--with-sysroot=%s' % sysroot
            ])

        if linkage:
            if linkage == 'static':
                configure_args.append('--disable-shared')
                configure_args.append('--enable-static')
            elif linkage == 'dynamic':
                configure_args.append('--disable-static')
                configure_args.append('--enable-shared')
            else:
                raise ValueError('unknown linkage')

        subprocess.check_call(['./configure'] + configure_args)

    def build(self, output_directory):
        make_args = get_make_jobs_args(self)

        binary_paths = self.target().platform.binary_paths(self.target().architecture)
        if len(binary_paths) > 0:
            make_args.append('PATH=%s:%s' % (':'.join(binary_paths), os.environ['PATH']))

        subprocess.check_call(['make'] + self.project_targets() + make_args)
        subprocess.check_call(['make', 'install'] + make_args)

    def __available_configure_host(self, candidates):
        with open(os.path.join(self.directory(), 'configure'), 'r') as file:
            contents = file.read()
            for candidate in candidates:
                if contents.find(candidate) >= 0:
                    return candidate

        return None
