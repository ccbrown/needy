import pipes
import Project
import os
import shlex
import subprocess


class SourceProject(Project.Project):
    def __init__(self, definition, needy):
        super().__init__(definition, needy)
        self.compilation_flags = []

        if self.target().platform == 'iphone':
            self.c_compiler = 'xcrun -sdk iphoneos clang'
            self.cpp_compiler = 'xcrun -sdk iphoneos clang++'
            self.compilation_flags = ['-arch', self.target().architecture]
        elif self.target().platform == 'android':
            toolchain = self.needy.android_toolchain_path(self.target().architecture)
            sysroot = self.needy.android_sysroot_path(self.target().architecture)

            if self.target().architecture.find('arm') >= 0:
                self.c_compiler = os.path.join(toolchain, 'bin', 'arm-linux-androideabi-gcc') + (' --sysroot=%s' % sysroot)
                self.cpp_compiler = os.path.join(toolchain, 'bin', 'arm-linux-androideabi-g++') + (' --sysroot=%s' % sysroot)
                self.compilation_flags = ['-mthumb', '-march=%s' % self.target().architecture]
            else:
                raise ValueError('unsupported architecture')
        else:
            self.c_compiler = 'clang'
            self.cpp_compiler = 'clang++'

        if 'source-directory' in self.definition.configuration:
            self.source_directory = self.definition.configuration['source-directory']
        elif os.path.exists(os.path.join(self.directory(), 'src')):
            self.source_directory = os.path.join(self.directory(), 'src')
        elif os.path.exists(os.path.join(self.directory(), 'source')):
            self.source_directory = os.path.join(self.directory(), 'source')
        else:
            raise ValueError('unable to deduce source directory')

        self.header_directory = self.source_directory
        if os.path.exists(os.path.join(self.directory(), 'include')):
            self.header_directory = os.path.join(self.directory(), 'include')
        elif os.path.exists(os.path.join(self.directory(), 'headers')):
            self.header_directory = os.path.join(self.directory(), 'headers')

    @staticmethod
    def is_project(definition):
        valid_source_dirs = ['source', 'src']
        if 'source-directory' in definition.configuration:
            valid_source_dirs += definition.configuration['source-directory']

        for src_dir in valid_source_dirs:
            if os.path.exists(os.path.join(definition.directory, src_dir)):
                return True
        return False

    def build(self, output_directory):
        object_directory = os.path.join(output_directory, 'obj')
        os.makedirs(object_directory)

        objects = []

        for root, dirs, files in os.walk(self.source_directory):
            for file in files:
                input = os.path.join(root, file)
                output = os.path.join(object_directory, os.path.relpath(input, self.source_directory))
                name, extension = os.path.splitext(output)
                output = name + '.o'

                if self.__compile(input, output):
                    objects.append(output)

        # TODO: link objects, copy headers
        raise ValueError('not fully unimplemented')

    def __compile(self, input, output):
        name, extension = os.path.splitext(input)

        if not os.path.exists(os.path.dirname(output)):
            os.makedirs(os.path.dirname(output))

        if extension == '.c':
            self.__printed_call(shlex.split(self.c_compiler) + self.compilation_flags + ['-c', input, '-o', output, '-I%s' % self.header_directory])
        elif extension == '.cpp':
            self.__printed_call(shlex.split(self.cpp_compiler) + self.compilation_flags + ['-c', input, '-o', output, '-I%s' % self.header_directory])
        else:
            return False

        return True

    def __printed_call(self, call):
        print ' '.join(pipes.quote(s) for s in call)
        subprocess.check_call(call)
