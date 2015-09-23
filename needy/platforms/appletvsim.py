from ..platform import Platform

import platform

DEFAULT_MIN_TVOS_VERSION = '9.0'


class AppleTVSimulatorPlatform(Platform):
    def __init__(self, parameters):
        Platform.__init__(self, parameters)
        self.__minimum_version = parameters.minimum_tvos_version if 'minimum_tvos_version' in parameters else DEFAULT_MIN_TVOS_VERSION

    @staticmethod
    def identifier():
        return 'appletvsim'

    def default_architecture(self):
        return platform.machine()

    def c_compiler(self, architecture):
        return 'xcrun -sdk appletvsimulator clang -arch %s -mtvos-version-min=%s' % (architecture, self.__minimum_version)

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk appletvsimulator clang++ -arch %s -mtvos-version-min=%s' % (architecture, self.__minimum_version)

    @staticmethod
    def detection_macro(architecture):
        return 'TARGET_OS_TV && TARGET_OS_SIMULATOR'
