import binascii
import hashlib
import json
import os
import shutil

from .process import command


class UniversalBinary:
    def __init__(self, name, libraries, needy):
        self.__name = name
        self.__libraries = libraries
        self.needy = needy

    def name(self):
        return self.__name

    def libraries(self):
        return self.__libraries

    def build_directory(self):
        return os.path.join(self.__libraries[0].directory(), 'build', 'universal', self.name())

    def include_path(self):
        return os.path.join(self.build_directory(), 'include')

    def library_path(self):
        return os.path.join(self.build_directory(), 'lib')

    def is_up_to_date(self):
        if self.needy.parameters().force_build:
            return False

        if not os.path.isfile(self.build_status_path()):
            return False

        with open(self.build_status_path(), 'r') as status_file:
            status_text = status_file.read()
            if not status_text.strip():
                return False
            status = json.loads(status_text)
            if 'configuration' not in status or binascii.unhexlify(status['configuration']) != self.configuration_hash():
                return False

        return True

    def build_status_path(self):
        return os.path.join(self.build_directory(), 'needy.status')

    def build(self):
        print('Building universal binary %s' % self.name())

        universal_paths = dict()

        for library in self.libraries():
            for root, dirs, files in os.walk(library.build_directory()):
                for path in files + dirs:
                    key = os.path.join(os.path.relpath(root, library.build_directory()), path)
                    if key not in universal_paths:
                        universal_paths[key] = []
                    universal_paths[key].append((library.target(), os.path.join(root, path)))

        directory = self.build_directory()

        if os.path.exists(directory):
            shutil.rmtree(directory)

        os.makedirs(directory)

        try:
            for path, builds in universal_paths.items():
                if len(builds) != len(self.libraries()):
                    continue

                file_name, extension = os.path.splitext(path)
                output_path = os.path.join(directory, path)

                self.__make_output_dirs_for_builds(output_path, builds)

                if any([os.path.isdir(source_path) for _, source_path in builds]):
                    continue

                if len(self.libraries()) == 1:
                    print('Copying %s' % path)
                    source_path = builds[0][1]
                    if os.path.islink(source_path):
                        os.symlink(os.readlink(source_path), output_path)
                    else:
                        shutil.copy(source_path, output_path)
                elif extension in ['.a', '.dylib', '.so']:
                    print('Creating universal library %s' % path)
                    command(['lipo', '-create'] + [lib for target, lib in builds] + ['-output', output_path])
                elif extension in ['.h', '.hpp', '.ipp']:
                    header_contents = '#if __APPLE__\n#include "TargetConditionals.h"\n#endif\n'
                    for target, header in builds:
                        macro = target.platform.detection_macro(target.architecture)
                        if not macro:
                            header_contents = ''
                            break
                        header_path = os.path.relpath(header, os.path.dirname(output_path))
                        header_contents += '#if {}\n#include "{}"\n#endif\n'.format(macro, header_path)
                    if header_contents:
                        print('Creating universal header %s' % path)
                        with open(output_path, 'w') as f:
                            f.write(header_contents)
        except:
            shutil.rmtree(directory)
            raise

        with open(self.build_status_path(), 'w') as status_file:
            status = {
                'configuration': binascii.hexlify(self.configuration_hash())
            }
            json.dump(status, status_file)

    def __make_output_dirs_for_builds(self, output_path, builds):
        for _, source_dir in builds:
            dir = output_path if os.path.isdir(source_dir) else os.path.dirname(output_path)
            if not os.path.exists(dir):
                os.makedirs(dir)

    def configuration_hash(self):
        hash = hashlib.sha256()

        for library in self.libraries():
            hash.update(library.configuration_hash())

        return hash.digest()
