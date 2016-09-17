from ..generator import Generator

import logging
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

        packages, broken_package_names = self.__get_pkgconfig_packages(env=env)
        owned_packages = self.__get_owned_packages(needy, packages)

        if broken_package_names:
            logging.warn('broken packages found: {}'.format(' '.join(broken_package_names)))

        contents = self.__get_header(self.__escape(env.get('PKG_CONFIG_PATH', '')))
        contents += self.__get_pkg_actions(needy, packages)
        contents += self.__get_pkgconfig_rules(needy, packages, owned_packages, broken_package_names)

        with open(path, 'w') as f:
            f.write(contents)

    @classmethod
    def __get_pkgconfig_packages(cls, env):
        packages = []
        broken_package_names = []

        package_names = [line.split()[0] for line in subprocess.check_output(['pkg-config', '--list-all'], env=env).decode().splitlines()]
        for package in package_names:
            try:
                pkg = {}
                pkg['name'] = package
                pkg['location'] = os.path.realpath(subprocess.check_output(['pkg-config', package, '--variable=pcfiledir'], env=env).decode().strip())
                pkg['cflags'] = subprocess.check_output(['pkg-config', package, '--cflags'], env=env).decode().strip()
                pkg['ldflags'] = subprocess.check_output(['pkg-config', package, '--libs', '--static'], env=env).decode().strip()
                packages.append(pkg)
            except subprocess.CalledProcessError:
                broken_package_names.append(package)
                continue
        return packages, broken_package_names

    @classmethod
    def __get_owned_packages(cls, needy, packages):
        owned_packages = []
        for package in packages:
            if not os.path.relpath(package['location'], os.path.realpath(needy.needs_directory())).startswith('..'):
                owned_packages.append(package)
        return owned_packages

    @classmethod
    def __get_header(cls, pkg_config_path):
        return textwrap.dedent('''\
            INSTALL_PREFIX = [ option.get prefix : "/usr/local" ] ;
            PKG_CONFIG_PATH = "{pkg_config_path}" ;

            import notfile ;
            import project ;

            local p = [ project.current ] ;

        ''').format(
            pkg_config_path=pkg_config_path
        )

    @classmethod
    def __get_pkg_actions(cls, needy, packages):
        rules = ''
        for package in packages:
            rules += 'alias {}-package : : : : <cflags>"{}" <linkflags>"{}" ;\n'.format(package['name'], PkgConfigJamGenerator.__escape(package['cflags']), PkgConfigJamGenerator.__escape(package['ldflags']))
            rules += textwrap.dedent('''\
                actions install-{package}-package-action {{ mkdir -p $(INSTALL_PREFIX) && cp -pR {package_prefix}/* $(INSTALL_PREFIX)/ }}
                notfile.notfile install-{package}-package : @$(__name__).install-{package}-package-action ;
            ''').format(package=package['name'], package_prefix=os.path.dirname(os.path.dirname(package['location'])))
            if not os.path.relpath(package['location'], os.path.realpath(needy.needs_directory())).startswith('..'):
                rules += 'alias install-{package}-package-if-owned : install-{package}-package ;\n'.format(package=package['name'])
            else:
                rules += 'alias install-{package}-package-if-owned ;\n'.format(package=package['name'])
            rules += textwrap.dedent('''\
                $(p).mark-target-as-explicit install-{package}-package install-{package}-package-if-owned ;

            ''').format(package=package['name'])
        return rules

    @classmethod
    def __get_pkgconfig_rules(cls, needy, packages, owned_packages, broken_package_names):
        return textwrap.dedent('''\
            PKG_CONFIG_PACKAGES = {pkg_config_packages} ;
            OWNED_PKG_CONFIG_PACKAGES = {owned_pkg_config_packages} ;

            rule dependency ( name : packages * ) {{
                if ! $(packages) {{
                    packages = $(name) ;
                }}
                if $(packages) in $(PKG_CONFIG_PACKAGES) {{
                    alias $(name) : $(packages)-package ;
                    alias install-$(name)-if-owned : install-$(packages)-package-if-owned ;

                    local p = [ project.current ] ;
                    $(p).mark-target-as-explicit install-$(name)-if-owned ;
                }}
            }}
        ''').format(
            pkg_config_packages=' '.join([package['name'] for package in packages if package['name'] not in broken_package_names]),
            owned_pkg_config_packages=' '.join([p['name'] for p in owned_packages])
        )

    @classmethod
    def __escape(cls, s):
        return s.replace('\\', '\\\\').replace('"', '\\"')
