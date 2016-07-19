from .xcode import XcodePlatform

import platform


class iOSPlatform(XcodePlatform):
    def __init__(self, parameters={}):
        XcodePlatform.__init__(self, parameters)

    @staticmethod
    def identifier():
        return 'ios'

    @staticmethod
    def sdk():
        return 'iphoneos'

    @staticmethod
    def os_name():
        return 'ios'

    @staticmethod
    def minimum_version():
        return '7.0'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-ios-version', default=iOSPlatform.minimum_version(),
                            help='the minimum iOS version to build for')

    @staticmethod
    def detection_macro(architecture):
        if architecture == 'arm64':
            return 'TARGET_OS_IOS && !TARGET_OS_SIMULATOR && __LP64__'
        elif architecture == 'armv7':
            return 'TARGET_OS_IOS && !TARGET_OS_SIMULATOR && !__LP64__'
        return None

    def default_architecture(self):
        return 'arm64'


class iOSSimulatorPlatform(iOSPlatform):
    @staticmethod
    def identifier():
        return 'iossimulator'

    @staticmethod
    def sdk():
        return 'iphonesimulator'

    @staticmethod
    def add_arguments(parser):
        pass

    @staticmethod
    def detection_macro(architecture):
        if architecture == 'x86_64':
            return 'TARGET_OS_IOS && TARGET_OS_SIMULATOR && __LP64__'
        elif architecture == 'i386':
            return 'TARGET_OS_IOS && TARGET_OS_SIMULATOR && !__LP64__'
        return None

    def default_architecture(self):
        return platform.machine()
