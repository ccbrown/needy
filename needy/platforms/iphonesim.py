from ..platform import Platform

import platform

DEFAULT_MIN_IOS_VERSION = '5.0'


class iPhoneSimulatorPlatform(Platform):
    def __init__(self, parameters):
        Platform.__init__(self, parameters)
        self.__minimum_version = parameters.minimum_ios_version if 'minimum_ios_version' in parameters else DEFAULT_MIN_IOS_VERSION

    @staticmethod
    def identifier():
        return 'iphonesim'

    def default_architecture(self):
        return platform.machine()

    def c_compiler(self, architecture):
        return 'xcrun -sdk iphonesimulator clang -arch %s -mios-version-min=%s' % (architecture, self.__minimum_version)

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk iphonesimulator clang++ -arch %s -mios-version-min=%s' % (architecture, self.__minimum_version)

    @staticmethod
    def detection_macro(architecture):
        if architecture == 'x86_64':
            return 'TARGET_OS_IOS && TARGET_OS_SIMULATOR && __LP64__'
        elif architecture == 'i386':
            return 'TARGET_OS_IOS && TARGET_OS_SIMULATOR && !__LP64__'
        return None
