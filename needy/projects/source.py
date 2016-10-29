import fnmatch
import pipes
import os
import shlex
import shutil
import logging

from distutils import dir_util
from .. import project


class SourceProject(project.Project):

    @staticmethod
    def identifier():
        return 'source'

    @staticmethod
    def source_directory(directory, configuration):
        if 'source-directory' in configuration:
            return configuration['source-directory']
        for name in SourceProject.__default_source_directory_names():
            if os.path.exists(os.path.join(directory, name)):
                return os.path.join(directory, name)
        return None

    @staticmethod
    def __default_header_directory_names():
        return ['include', 'headers']

    @staticmethod
    def __default_source_directory_names():
        return ['src', 'source']

    @staticmethod
    def header_directory(directory, configuration):
        if 'header-directory' in configuration:
            return configuration['header-directory']
        for name in SourceProject.__default_header_directory_names():
            if os.path.exists(os.path.join(directory, name)):
                return os.path.join(directory, name)
        return SourceProject.source_directory(directory, configuration)

    @staticmethod
    def copy_headers(directory, configuration, destination):
        source_directory = SourceProject.source_directory(directory, configuration)
        header_directory = SourceProject.header_directory(directory, configuration)

        logging.info('Copying headers from {}'.format(header_directory))

        if header_directory != source_directory:
            dir_util.copy_tree(header_directory, destination)
        else:
            def non_headers(directory, files):
                return [f for f in files if os.path.isfile(os.path.join(directory, f)) and os.path.splitext(f)[1] not in ['.h', '.hh', '.hpp']]
            if os.path.exists(destination):
                shutil.rmtree(destination)
            shutil.copytree(header_directory, destination, ignore=non_headers)

    @staticmethod
    def is_valid_project(definition, needy):
        header_dir = SourceProject.header_directory(definition.directory, definition.configuration)
        if header_dir is None:
            search_paths = SourceProject.__default_header_directory_names() + SourceProject.__default_source_directory_names()
            return False, 'no header path found in {} and none specified'.format(search_paths)
        return True, 'headers found in {}'.format(header_dir)

    @staticmethod
    def configuration_keys():
        return project.Project.configuration_keys() | {'source-directory', 'header-directory', 'exclude'}

    def build(self, output_directory):
        # check for needs

        if self.needy.find_needs_file(self.directory()):
            needy = Needy(self.directory(), self.needy.parameters())
            needy.satisfy_target(self.target())

        # compile source

        source_directory = self.source_directory(self.directory(), self.configuration())
        header_directory = self.header_directory(self.directory(), self.configuration())

        include_paths = []
        if header_directory != source_directory:
            include_paths.append(header_directory)

        if source_directory:
            include_paths.append(source_directory)
            object_directory = os.path.join(output_directory, 'obj')
            os.makedirs(object_directory)

            objects = []

            for root, dirs, files in os.walk(source_directory):
                for file in files:
                    input = os.path.join(root, file)
                    relpath = os.path.relpath(input, source_directory)
                    if self.__should_exclude(relpath):
                        continue
                    output = os.path.join(object_directory, relpath)
                    name, extension = os.path.splitext(output)
                    output = name + '.o'

                    if self.__compile(input, output, include_paths):
                        objects.append(output)

            if len(objects) > 0:
                self.__link(objects, os.path.join(output_directory, 'lib'))

        self.copy_headers(self.directory(), self.configuration(), os.path.join(output_directory, 'include'))

    def __compile(self, input, output, include_paths):
        name, extension = os.path.splitext(input)

        if not os.path.exists(os.path.dirname(output)):
            os.makedirs(os.path.dirname(output))

        platform = self.target().platform
        architecture = self.target().architecture

        logging.info('Compiling {}'.format(input))

        if platform.identifier() == 'windows':
            flags = ['/c', input, '/Fo{}'.format(output), '/Ox'] + ['/I{}'.format(path) for path in include_paths]
        else:
            flags = ['-c', input, '-o', output, '-O3'] + ['-I{}'.format(path) for path in include_paths]

        if extension == '.c':
            if 'CFLAGS' in os.environ:
                flags.extend(shlex.split(os.environ['CFLAGS']))
            self.command((['needy-cc'] if platform.identifier() != 'windows' else platform.c_compiler(architecture)) + flags, verbosity=logging.DEBUG)
        elif extension == '.cpp':
            if 'CXXFLAGS' in os.environ:
                flags.extend(shlex.split(os.environ['CXXFLAGS']))
            self.command((['needy-cxx'] if platform.identifier() != 'windows' else platform.cxx_compiler(architecture)) + flags, verbosity=logging.DEBUG)
        else:
            return False

        return True

    def __link(self, objects, lib_directory):
        platform = self.target().platform
        architecture = self.target().architecture

        name = os.path.basename(os.path.dirname(self.directory()))

        output = os.path.join(lib_directory, ('{}.lib' if platform.identifier() == 'windows' else 'lib{}.a').format(name))
        logging.info('Linking {}'.format(output))

        if platform.identifier() == 'windows':
            self.command(['lib'] + objects + ['-OUT:{}'.format(output)], verbosity=logging.DEBUG)
        else:
            self.command(['ar', '-rv', output] + objects, verbosity=logging.DEBUG)

    def __should_exclude(self, path):
        if 'exclude' in self.configuration():
            for pattern in self.evaluate(self.configuration()['exclude']):
                if fnmatch.fnmatch(path, pattern):
                    return True
        return False
