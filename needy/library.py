import binascii
import hashlib
import json
import os
import shutil
import logging
import tarfile
import textwrap

from operator import itemgetter

from .filesystem import TempDir

from .project import evaluate_conditionals
from .project import ProjectDefinition

from .sources.download import Download
from .sources.directory import Directory
from .sources.git import GitRepository

from .cd import cd
from .override_environment import OverrideEnvironment
from .target import Target
from .filesystem import clean_directory

from .process import command
from .projects import project_types

from .utility import Fore

class Library:
    def __init__(self, needy, name, target=None, configuration=None, development_mode=False, build_caches=[]):
        self.needy = needy
        self.__name = name
        self.__target = target
        self.__configuration = configuration
        self.__directory = os.path.join(needy.needs_directory(), name)
        self.__development_mode = development_mode
        self.__build_caches = build_caches

    def configuration(self):
        return self.__configuration

    def name(self):
        return self.__name

    def target(self):
        return self.__target

    def project_configuration(self):
        return evaluate_conditionals(self.__configuration['project'] if 'project' in self.__configuration else dict(), self.target())

    def dependencies(self):
        str_or_list = self.configuration().get('dependencies', [])
        return str_or_list if isinstance(str_or_list, list) else [str_or_list]

    def string_format_variables(self):
        return {
            'build_directory': self.build_directory(),
            'platform': self.target().platform.identifier(),
            'architecture': self.target().architecture,
            'needs_file_directory': self.needy.path(),
            'build_concurrency': self.needy.build_concurrency(),
        }

    @staticmethod
    def additional_project_configuration_keys():
        """ the configuration keys that we handle here instead of in Project classes (usually because we need them before determining the project type) """
        return {'post-clean', 'configure-steps', 'environment', 'type', 'root'}

    def evaluate(self, str_or_list, **kwargs):
        l = [] if not str_or_list else (str_or_list if isinstance(str_or_list, list) else [str_or_list])
        variables = self.string_format_variables()
        variables.update(kwargs)
        return [str.format(**variables) for str in l]

    def clean_source(self):
        source = self.source()
        source.clean()

    def clean_build(self):
        clean_directory(self.build_directory())

    def initialize_source(self):
        self.clean_source()
        with OverrideEnvironment(self.__environment_overrides()):
            self.__post_clean()

    def synchronize_source(self):
        source = self.source()
        source.synchronize()

    def source(self):
        cfg = self.__configuration
        if 'download' in cfg:
            return Download(cfg['download'], cfg['checksum'], self.source_directory(), os.path.join(self.directory(), 'download'))
        if 'repository' in cfg:
            return GitRepository(cfg['repository'], cfg['commit'], self.source_directory())
        if 'directory' in cfg:
            return Directory(cfg['directory'] if os.path.isabs(cfg['directory']) else os.path.join(self.needy.path(), cfg['directory']), self.source_directory())
        raise ValueError('no source specified in configuration')

    def build(self):
        if not self.needy.parameters().force_build and not self.is_in_development_mode():
            if self.__load_cached_artifacts():
                logging.info('Build restored from cache')
                return True

        logging.info('Building for %s %s' % (self.target().platform.identifier(), self.target().architecture))

        if ' ' in self.__directory:
            print(Fore.YELLOW + '[WARNING]' + Fore.RESET + ' The build path contains spaces. Some build systems don\'t '
                  'handle spaces well, so if you have problems, consider moving the project or using a symlink.')

        if not self.is_in_development_mode():
            self.clean_source()

        with OverrideEnvironment(self.__environment_overrides()):
            if not self.is_in_development_mode():
                self.__post_clean()

            configuration = self.project_configuration()

            project = self.project(ProjectDefinition(self.target(), self.project_root(), configuration))
            if not project:
                raise RuntimeError('unknown project type')

            unrecognized_configuration_keys = set(configuration.keys()) - project.configuration_keys() - self.additional_project_configuration_keys()
            if len(unrecognized_configuration_keys):
                raise RuntimeError('unrecognized project configuration keys: {}'.format(', '.join(unrecognized_configuration_keys)))

            project.set_string_format_variables(**self.string_format_variables())

            if not self.is_in_development_mode():
                self.clean_build()

            self.__actualize(project)
            self.__write_build_status()
            if not self.is_in_development_mode():
                self.__cache_artifacts()

        return True

    def __post_clean(self):
        configuration = self.project_configuration()
        post_clean_commands = configuration['post-clean'] if 'post-clean' in configuration else []
        with cd(self.project_root()):
            for cmd in self.evaluate(post_clean_commands):
                command(cmd)

    def __actualize(self, project):
        build_directory = self.build_directory()
        configuration = self.project_configuration()
        with cd(self.project_root()):
            try:
                project.setup()
                if 'configure-steps' in configuration:
                    project.run_commands(configuration['configure-steps'])
                else:
                    project.configure(build_directory)
                project.pre_build(build_directory)
                project.build(build_directory)
                project.post_build(build_directory)
                Library.make_pkgconfigs_relocatable(build_directory)
                if self.__should_generate_pkgconfig():
                    self.generate_pkgconfig(build_directory, self.name())
            except:
                shutil.rmtree(build_directory)
                raise

    def __should_generate_pkgconfig(self):
        def is_empty(path):
            return not os.path.exists(path) or len(os.listdir(path)) == 0
        lib_dir = os.path.join(self.build_directory(), 'lib')
        include_dir = os.path.join(self.build_directory(), 'include')
        return (is_empty(os.path.join(lib_dir, 'pkgconfig')) and
                (not is_empty(include_dir) or not is_empty(lib_dir)))

    def __write_build_status(self):
        with open(self.build_status_path(), 'w') as status_file:
            status = {} if self.is_in_development_mode() else self.configuration_dict()
            json.dump(status, status_file, sort_keys=True, indent=4, separators=(',', ': '))

    def __cache_artifacts(self):
        if not self.__build_caches:
            return False
        with TempDir() as temp_dir:
            temp_tar = os.path.join(temp_dir, 'temp')
            tar = tarfile.open(temp_tar, 'w:gz')
            tar.add(self.build_directory(), arcname='.')
            tar.close()
            for cache in self.__build_caches:
                if cache.set(self.__cache_key(), temp_tar):
                    d = self.configuration_dict()
                    logging.debug('cache object hash {} formed from...\n{}'.format(
                        binascii.hexlify(self.configuration_hash(d)),
                        json.dumps(d, sort_keys=True, indent=4, separators=(',', ': ')))
                    )
                    return True
        return False

    def __load_cached_artifacts(self):
        with TempDir() as temp_dir:
            temp_tar = os.path.join(temp_dir, 'artifacts.tgz')
            for cache in self.__build_caches:
                if cache.get(self.__cache_key(), temp_tar):
                    tar = tarfile.open(temp_tar, 'r:gz')
                    tar.extractall(path=self.build_directory())
                    tar.close()
                    return True
        return False

    def __cache_key(self):
        configuration_hash = binascii.hexlify(self.configuration_hash()).decode()
        path = os.path.relpath(self.build_directory(), self.needy.needs_directory())
        return os.path.join(path, configuration_hash)

    def __environment_overrides(self):
        configuration = self.project_configuration()
        overrides = self.target().platform.environment_overrides(self.target().architecture)
        if 'environment' in configuration:
            for key, value in configuration['environment'].items():
                overrides[key] = self.evaluate(value, current=overrides.get(key, os.environ.get(key, '')))[0]
        self.__log_environment_overrides(overrides)

        dependencies = self.dependencies()
        dependencies_to_provide = [dependency for dependency in dependencies if not self.needy.library_is_overridden(dependency)]
        if dependencies_to_provide:
            pkg_config_path = overrides['PKG_CONFIG_PATH'] if 'PKG_CONFIG_PATH' in overrides else os.environ.get('PKG_CONFIG_PATH', '')
            dependency_config_path = self.needy.pkg_config_path(self.target(), dependencies_to_provide)
            overrides['PKG_CONFIG_PATH'] = (dependency_config_path + ':' + pkg_config_path) if pkg_config_path and dependency_config_path else dependency_config_path

        return overrides

    def __log_environment_overrides(self, overrides, verbosity=logging.DEBUG):
        if overrides is not None and len(overrides) > 0:
            logging.log(verbosity, 'Overriding environment with new variables:')
            for k, v in overrides.items():
                logging.log(verbosity, '{}={}'.format(k, v))

    def is_in_development_mode(self):
        return self.__development_mode

    def is_up_to_date(self):
        if self.is_in_development_mode():
            return False
        d = self.status_dict()
        return d and self.configuration_hash(d) == self.configuration_hash()

    def status_dict(self):
        if not os.path.isfile(self.build_status_path()):
            return None
        with open(self.build_status_path(), 'r') as status_file:
            status_text = status_file.read()
            if not status_text.strip():
                return None
            return json.loads(status_text)

    def status_text(self):
        if self.is_in_development_mode():
            return 'dev mode'
        if self.is_up_to_date():
            return 'up-to-date'
        return 'out-of-date'

    def substatus_texts(self):
        ret = {}
        if self.is_in_development_mode():
            status = self.source().status_text()
            if status:
                ret[os.path.relpath(self.source_directory())] = '{}: {}'.format(self.source().identifier(), status)
            else:
                ret[os.path.relpath(self.source_directory())] = '{}'.format(self.source().identifier())
        return ret

    def directory(self):
        return self.__directory

    def build_directory(self):
        directory = os.path.join(self.__directory, 'build', self.target().platform.identifier(), self.target().architecture)
        suffix = self.configuration().get('build-directory-suffix')
        if suffix:
            directory = os.path.join(directory, suffix.lstrip(os.path.sep))
        return directory

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
        candidates = project_types

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
                        print(Fore.YELLOW + '[WARNING]' + Fore.RESET + ' Detected {} project, but the following prerequisites are missing: {}'.format(
                            candidate.identifier(), ', '.join(missing_prerequisites)
                        ))
                        continue
                    return candidate(definition, self.needy)

        raise RuntimeError('unknown project type')

    @classmethod
    def build_compatibility(cls):
        return 6

    def configuration_hash(self, config_dict=None):
        hash = hashlib.sha256()
        hash.update(json.dumps(config_dict or self.configuration_dict(), sort_keys=True).encode())
        return hash.digest()

    def configuration_dict(self):
        configuration = self.__configuration.copy()
        configuration['project'] = self.project_configuration()
        return {
            'build-compatibility': self.build_compatibility(),
            'platform-configuration': (self.target().platform.configuration(self.target().architecture) or {}),
            'library-configuration': configuration,
            'dependencies': [self.needy.library_configuration(self.target(), d) for d in self.dependencies()],
        }

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
                        prefix=${{pcfiledir}}/../..
                        exec_prefix=${{prefix}}
                        libdir=${{exec_prefix}}/lib
                        includedir=${{prefix}}/include

                        Name: {name}
                        Version: {version}
                        Description: {name}
                        Libs: -L${{libdir}} {lflags}
                        Cflags: -I${{includedir}}
                    """.format(name=name, version=0, lflags=' '.join([('-l'+lib_name) for lib_name in libs]))))

    @staticmethod
    def make_pkgconfigs_relocatable(build_dir):
        if os.path.exists(build_dir):
            for dirname, subdirs, files in os.walk(os.path.join(build_dir, 'lib')):
                for filename in files:
                    if filename.endswith('.pc'):
                        pc = ''
                        with open(os.path.join(dirname, filename), 'r') as f:
                            pc = f.read().replace(build_dir, '${pcfiledir}/../..')
                        with open(os.path.join(dirname, filename), 'w+') as f:
                            f.write(pc)
