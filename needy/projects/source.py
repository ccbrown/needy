import pipes
import os
import shlex
import shutil

from .. import project


class SourceProject(project.Project):

    @staticmethod
    def identifier():
        return 'source'

    @staticmethod
    def source_directory(directory, configuration):
        if 'source-directory' in configuration:
            return configuration['source-directory']
        elif os.path.exists(os.path.join(directory, 'src')):
            return os.path.join(directory, 'src')
        elif os.path.exists(os.path.join(directory, 'source')):
            return os.path.join(directory, 'source')
        return None

    @staticmethod
    def header_directory(directory, configuration):
        if 'header-directory' in configuration:
            return configuration['header-directory']
        elif os.path.exists(os.path.join(directory, 'include')):
            return os.path.join(directory, 'include')
        elif os.path.exists(os.path.join(directory, 'headers')):
            return os.path.join(directory, 'headers')
        return SourceProject.source_directory(directory, configuration)

    @staticmethod
    def copy_headers(directory, configuration, destination):
        source_directory = SourceProject.source_directory(directory, configuration)
        header_directory = SourceProject.header_directory(directory, configuration)

        if header_directory != source_directory:
            shutil.copytree(header_directory, destination)
        else:
            def non_headers(directory, files):
                return [f for f in files if os.path.isfile(os.path.join(directory, f)) and os.path.splitext(f)[1] not in ['.h', '.hh', '.hpp']]
            shutil.copytree(header_directory, destination, ignore=non_headers)

    @staticmethod
    def is_valid_project(definition, needy):
        return SourceProject.header_directory(definition.directory, definition.configuration)

    @staticmethod
    def configuration_keys():
        return ['source-directory', 'header-directory']

    def build(self, output_directory):
        # check for needs

        needy = self.needy.recursive(self.directory())
        if needy:
            needy.satisfy_target(self.target())

        # compile source

        source_directory = self.source_directory(self.directory(), self.configuration())
        header_directory = self.header_directory(self.directory(), self.configuration())

        additional_flags = ['-I%s' % source_directory]
        if header_directory != source_directory:
            additional_flags.append('-I%s' % header_directory)

        if source_directory:
            object_directory = os.path.join(output_directory, 'obj')
            os.makedirs(object_directory)

            objects = []

            for root, dirs, files in os.walk(source_directory):
                for file in files:
                    input = os.path.join(root, file)
                    output = os.path.join(object_directory, os.path.relpath(input, source_directory))
                    name, extension = os.path.splitext(output)
                    output = name + '.o'

                    if self.__compile(input, output, additional_flags):
                        objects.append(output)

            if len(objects) > 0:
                # TODO: link objects
                raise NotImplementedError('not fully unimplemented')

        # copy headers
        self.copy_headers(self.directory(), self.configuration(), os.path.join(output_directory, 'include'))

    def __compile(self, input, output, additional_flags):
        name, extension = os.path.splitext(input)

        if not os.path.exists(os.path.dirname(output)):
            os.makedirs(os.path.dirname(output))

        if extension == '.c':
            self.__printed_call(shlex.split(self.target().platform.c_compiler(self.target().architecture)) + ['-c', input, '-o', output] + additional_flags)
        elif extension == '.cpp':
            self.__printed_call(shlex.split(self.target().platform.cxx_compiler(self.target().architecture)) + ['-c', input, '-o', output] + additional_flags)
        else:
            return False

        return True

    def __printed_call(self, call):
        print(' '.join(pipes.quote(s) for s in call))
        self.command(call)
