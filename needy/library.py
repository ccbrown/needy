import binascii
import hashlib
import json
import os
import shutil
import logging
import textwrap

from operator import itemgetter

try:
    from colorama import Fore
except ImportError:
    class EmptyStringAttributes:
        def __getattr__(self, name):
            return ''
    Fore = EmptyStringAttributes()

from .project import evaluate_conditionals
from .project import ProjectDefinition

from .sources.download import Download
from .sources.directory import Directory
from .sources.git import GitRepository

from .cd import cd
from .override_environment import OverrideEnvironment
from .target import Target

from .process import command

from .projects.androidmk import AndroidMkProject
from .projects.autotools import AutotoolsProject
from .projects.boostbuild import BoostBuildProject
from .projects.cmake import CMakeProject
from .projects.custom import CustomProject
from .projects.make import MakeProject
from .projects.source import SourceProject
from .projects.xcode import XcodeProject


class Library:
    def __init__(self, needy, name, target=None, configuration=None, development_mode=False):
        self.needy = needy
        self.__name = name
        self.__target = target
        self.__configuration = configuration
        self.__directory = os.path.join(needy.needs_directory(), name)
        self.__development_mode = development_mode

    def configuration(self):
        return self.__configuration

    def name(self):
        return self.__name

    def target(self):
        return self.__target

    def project_configuration(self):
        return evaluate_conditionals(self.__configuration['project'] if 'project' in self.__configuration else dict(), self.target())

    def string_format_variables(self):
        return {
            'build_directory': self.build_directory(),
            'platform': self.target().platform.identifier(),
            'architecture': self.target().architecture,
            'needs_file_directory': self.needy.path()
        }

    @staticmethod
    def additional_project_configuration_keys():
        """ the configuration keys that we handle here instead of in Project classes (usually because we need them before determining the project type) """
        return {'post-clean', 'environment', 'type', 'root'}

    def evaluate(self, str_or_list, **kwargs):
        l = [] if not str_or_list else (str_or_list if isinstance(str_or_list, list) else [str_or_list])
        variables = self.string_format_variables()
        variables.update(kwargs)
        return [str.format(**variables) for str in l]

    def clean_source(self):
        if 'download' in self.__configuration:
            source = Download(self.__configuration['download'], self.__configuration['checksum'], self.source_directory(), os.path.join(self.directory(), 'download'))
        elif 'repository' in self.__configuration:
            source = GitRepository(self.__configuration['repository'], self.__configuration['commit'], self.source_directory())
        elif 'directory' in self.__configuration:
            source = Directory(self.__configuration['directory'] if os.path.isabs(self.__configuration['directory']) else os.path.join(needy.path(), self.__configuration['directory']), self.source_directory())
        else:
            raise ValueError('no source specified in configuration')

        source.clean()

    def build(self):
        print('Building for %s %s' % (self.target().platform.identifier(), self.target().architecture))

        if ' ' in self.__directory:
            print(Fore.YELLOW + '[WARNING]' + Fore.RESET + ' The build path contains spaces. Some build systems don\'t '
                  'handle spaces well, so if you have problems, consider moving the project or using a symlink.')

        if not self.__development_mode:
            self.clean_source()

        configuration = self.project_configuration()
        env_overrides = self.__parse_env_overrides(configuration['environment'] if 'environment' in configuration else None)

        self.__log_env_overrides(env_overrides)
        with OverrideEnvironment(env_overrides):
            post_clean_commands = configuration['post-clean'] if 'post-clean' in configuration else []
            with cd(self.project_root()):
                for cmd in self.evaluate(post_clean_commands):
                    command(cmd)

            definition = ProjectDefinition(self.target(), self.project_root(), configuration)
            project = self.project(definition)

            unrecognized_configuration_keys = set(configuration.keys()) - project.configuration_keys() - self.additional_project_configuration_keys()
            if len(unrecognized_configuration_keys):
                raise RuntimeError('unrecognized project configuration keys: {}'.format(', '.join(unrecognized_configuration_keys)))

            project.set_string_format_variables(**self.string_format_variables())

            if not project:
                raise RuntimeError('unknown project type')

            build_directory = self.build_directory()

            if os.path.exists(build_directory):
                shutil.rmtree(build_directory)

            os.makedirs(build_directory)

            with cd(self.project_root()):
                try:
                    project.setup()
                    project.configure(build_directory)
                    project.pre_build(build_directory)
                    project.build(build_directory)
                    project.post_build(build_directory)
                    if not os.path.exists(os.path.join(build_directory, 'lib', 'pkgconfig')):
                        self.generate_pkgconfig(build_directory, self.name())
                except:
                    shutil.rmtree(build_directory)
                    raise

            with open(self.build_status_path(), 'w') as status_file:
                status = {
                    'configuration': binascii.hexlify(self.configuration_hash()).decode()
                }
                json.dump(status, status_file)

        return True

    def __parse_env_overrides(self, overrides):
        if overrides is None:
            return dict()
        ret = overrides.copy()
        for k, v in ret.items():
            ret[k] = self.evaluate(v, current=os.environ[k] if k in os.environ else '')[0]
        return ret

    def __log_env_overrides(self, env_overrides, verbosity=logging.DEBUG):
        if env_overrides is not None and len(env_overrides) > 0:
            logging.log(verbosity, 'Overriding environment with new variables:')
            for k, v in env_overrides.iteritems():
                logging.log(verbosity, '{}={}'.format(k, v))

    def has_up_to_date_build(self):
        if self.needy.parameters().force_build or not os.path.isfile(self.build_status_path()) or self.__development_mode:
            return False
        with open(self.build_status_path(), 'r') as status_file:
            status_text = status_file.read()
            if not status_text.strip():
                return False
            status = json.loads(status_text)
            if 'configuration' not in status or binascii.unhexlify(status['configuration']) != self.configuration_hash():
                return False
        return True

    def directory(self):
        return self.__directory

    def build_directory(self):
        return os.path.join(self.__directory, 'build', self.target().platform.identifier(), self.target().architecture)

    def build_status_path(self):
        return os.path.join(self.build_directory(), 'needy.status')

    def source_directory(self):
        return os.path.join(self.__directory, 'source')

    def project_root(self):
        configuration = self.project_configuration()
        return os.path.join(self.source_directory(), configuration['root']) if 'root' in configuration else self.source_directory()

    def include_path(self):
        return os.path.join(self.build_directory(), 'include')

    def library_path(self):
        return os.path.join(self.build_directory(), 'lib')

    def project(self, definition):
        candidates = [AndroidMkProject, AutotoolsProject, CMakeProject, BoostBuildProject, MakeProject, XcodeProject, SourceProject, CustomProject]

        if 'type' in definition.configuration:
            for candidate in candidates:
                if candidate.identifier() == definition.configuration['type']:
                    missing_prerequisites = candidate.missing_prerequisites(definition, self.needy)
                    if len(missing_prerequisites) > 0:
                        raise RuntimeError('missing prerequisites for explicit project type: {}'.format(', '.join(missing_prerequisites)))
                    return candidate(definition, self.needy)
            raise RuntimeError('unknown project type')

        scores = [(len(set(definition.configuration.keys()) & set(c.configuration_keys())), c) for c in candidates]
        candidates = [candidate for score, candidate in sorted(scores, key=itemgetter(0), reverse=True)]

        logging.debug('project candidates ordered by number of valid configuration keys: {}'.format(', '.join([c.identifier() for c in candidates])))
        logging.debug('evaluating candidates in {}'.format(definition.directory))
        with cd(definition.directory):
            for candidate in candidates:
                valid, reasons = candidate.is_valid_project(definition, self.needy)
                missing_prerequisites = candidate.missing_prerequisites(definition, self.needy)
                logging.debug('project type determined {} be {}'.format('to' if valid else 'not to', candidate.identifier()))
                if isinstance(reasons, list):
                    for r in reasons:
                        logging.debug('  - {}'.format(r))
                else:
                    logging.debug('  - {}'.format(reasons))
                if valid:
                    if len(missing_prerequisites) > 0:
                        print(Fore.YELLOW + '[WARNING]' + Fore.RESET + ' Detected {} project, but the following prerequisites are missing: {}'.format(candidate.identifier(), ', '.join(missing_prerequisites)))
                        continue
                    return candidate(definition, self.needy)

        raise RuntimeError('unknown project type')

    def configuration_hash(self):
        hash = hashlib.sha256()

        top = self.__configuration.copy()
        top.pop('project', None)
        hash.update(json.dumps(top, sort_keys=True).encode())

        hash.update(json.dumps(self.project_configuration(), sort_keys=True).encode())

        platform_configuration_hash = self.target().platform.configuration_hash(self.target().architecture)
        if platform_configuration_hash:
            hash.update(platform_configuration_hash)

        return hash.digest()

    @staticmethod
    def generate_pkgconfig(prefix, library_name):
        libs = []

        lib_path = os.path.join(prefix, 'lib')

        if os.path.exists(lib_path):
            for file in os.listdir(lib_path):
                name, ext = os.path.splitext(file)
                if os.path.isfile(os.path.join(lib_path, file)) and name.startswith('lib') and len(name) > 3:
                    lib_name = name[3:]
                    if lib_name not in libs:
                        libs.append(lib_name)

        packages = {lib_name: [lib_name] for lib_name in libs}
        if library_name not in packages:
            packages[library_name] = libs

        pkgconfig_path = os.path.join(prefix, 'lib', 'pkgconfig')

        for name, libs in packages.items():
            pc_path = os.path.join(pkgconfig_path, name+'.pc')
            if not os.path.exists(pc_path):
                if not os.path.exists(pkgconfig_path):
                    os.makedirs(pkgconfig_path)
                with open(pc_path, 'w') as f:
                    f.write(textwrap.dedent("""\
                        # This file was automatically generated by Needy.
                        prefix={prefix}
                        exec_prefix=${{prefix}}
                        libdir=${{exec_prefix}}/lib
                        includedir=${{prefix}}/include

                        Name: {name}
                        Version: {version}
                        Description: {name}
                        Libs: -L${{libdir}} {lflags}
                        Cflags: -I${{includedir}}
                    """.format(prefix=prefix, name=name, version=0, lflags=' '.join([('-l'+lib_name) for lib_name in libs]))))
