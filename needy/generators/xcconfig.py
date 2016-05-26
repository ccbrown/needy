from ..generator import Generator
from ..platform import available_platforms
from ..target import Target

import os


class XCConfigGenerator(Generator):

    @staticmethod
    def identifier():
        return 'xcconfig'

    def __xcconfig(self, needy, target, sdk, arch):
        header_search_paths = []
        library_search_paths = []
        for name, library in needy.libraries_to_build(target):
            header_search_paths.append(library.include_path())
            library_search_paths.append(library.library_path())
        ret = "NEEDY_HEADER_SEARCH_PATHS[sdk={},arch={}] = {}\n".format(sdk, arch, ' '.join(header_search_paths))
        ret += "NEEDY_LIBRARY_SEARCH_PATHS[sdk={},arch={}] = {}\n".format(sdk, arch, ' '.join(library_search_paths))
        ret += "HEADER_SEARCH_PATHS[sdk={},arch={}] = $(inherited) $(NEEDY_HEADER_SEARCH_PATHS)\n".format(sdk, arch)
        ret += "LIBRARY_SEARCH_PATHS[sdk={},arch={}] = $(inherited) $(NEEDY_LIBRARY_SEARCH_PATHS)\n".format(sdk, arch)
        ret += "\n"
        return ret

    def generate(self, needy):
        path = os.path.join(needy.needs_directory(), 'search-paths.xcconfig')

        contents = ''

        if 'osx' in available_platforms():
            contents += self.__xcconfig(needy, Target(needy.platform('osx'), 'i386'), 'macosx*', 'i386')
            contents += self.__xcconfig(needy, Target(needy.platform('osx'), 'x86_64'), 'macosx*', 'x86_64')

        if 'ios' in available_platforms():
            contents += self.__xcconfig(needy, Target(needy.platform('ios'), 'armv7'), 'iphoneos*', 'armv7')
            contents += self.__xcconfig(needy, Target(needy.platform('ios'), 'arm64'), 'iphoneos*', 'arm64')

        if 'iossimulator' in available_platforms():
            contents += self.__xcconfig(needy, Target(needy.platform('iossimulator'), 'i386'), 'iphonesimulator*', 'i386')
            contents += self.__xcconfig(needy, Target(needy.platform('iossimulator'), 'x86_64'), 'iphonesimulator*', 'x86_64')

        if 'tvos' in available_platforms():
            contents += self.__xcconfig(needy, Target(needy.platform('tvos'), 'arm64'), 'appletvos*', 'arm64')

        if 'tvossimulator' in available_platforms():
            contents += self.__xcconfig(needy, Target(needy.platform('tvossimulator'), 'i386'), 'appletvsimulator*', 'i386')
            contents += self.__xcconfig(needy, Target(needy.platform('tvossimulator'), 'x86_64'), 'appletvsimulator*', 'x86_64')

        with open(path, 'w') as xcconfig:
            xcconfig.write(contents)
