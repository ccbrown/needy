from ..generator import Generator

import os
import subprocess
import textwrap


class PkgConfigJamGenerator(Generator):

    @staticmethod
    def identifier():
        return 'pkgconfig-jam'

    def generate(self, needy):
        path = os.path.join(needy.needs_directory(), 'pkgconfig.jam')

        env = os.environ.copy()
        env['PKG_CONFIG_LIBDIR'] = ''

        contents = textwrap.dedent('''\
            INSTALL_PREFIX = [ option.get prefix : "/usr/local" ] ;
            PKG_CONFIG_PATH = "{pkg_config_path}" ;

            import notfile ;
            import project ;

            local p = [ project.current ] ;

        ''').format(
            pkg_config_path=self.__escape(env.get('PKG_CONFIG_PATH', ''))
        )

        packages = [line.split()[0] for line in subprocess.check_output(['pkg-config', '--list-all'], env=env).decode().splitlines()]
        owned_packages = []

        for package in packages:
            location = os.path.realpath(subprocess.check_output(['pkg-config', package, '--variable=pcfiledir'], env=env).decode().strip())
            cflags = subprocess.check_output(['pkg-config', package, '--cflags'], env=env).decode().strip()
            ldflags = subprocess.check_output(['pkg-config', package, '--libs', '--static'], env=env).decode().strip()
            contents += 'alias {}-package : : : : <cflags>"{}" <linkflags>"{}" ;\n'.format(package, self.__escape(cflags), self.__escape(ldflags))
            contents += textwrap.dedent('''\
                actions install-{package}-package-action {{ mkdir -p $(INSTALL_PREFIX) && cp -pR {package_prefix}/* $(INSTALL_PREFIX)/ }}
                notfile.notfile install-{package}-package : @$(__name__).install-{package}-package-action ;
            ''').format(package=package, package_prefix=os.path.dirname(os.path.dirname(location)))
            if not os.path.relpath(location, os.path.realpath(needy.needs_directory())).startswith('..'):
                owned_packages.append(package)
                contents += 'alias install-{package}-package-if-owned : install-{package}-package ;\n'.format(package=package)
            else:
                contents += 'alias install-{package}-package-if-owned ;\n'.format(package=package)
            contents += textwrap.dedent('''\
                $(p).mark-target-as-explicit install-{package}-package install-{package}-package-if-owned ;

            ''').format(package=package)

        contents += textwrap.dedent('''\
            PKG_CONFIG_PACKAGES = {pkg_config_packages} ;
            OWNED_PKG_CONFIG_PACKAGES = {owned_pkg_config_packages} ;

            rule dependency ( name : packages * ) {{
                if ! $(packages) {{
                    packages = $(name) ;
                }}
                alias $(name) : $(packages)-package ;
                alias install-$(name)-if-owned : install-$(packages)-package-if-owned ;

                local p = [ project.current ] ;
                $(p).mark-target-as-explicit install-$(name)-if-owned ;
            }}
        ''').format(
            pkg_config_packages=' '.join(packages),
            owned_pkg_config_packages=' '.join(owned_packages)
        )

        with open(path, 'w') as f:
            f.write(contents)

    @classmethod
    def __escape(cls, s):
        return s.replace('\\', '\\\\').replace('"', '\\"')
