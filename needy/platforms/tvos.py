from .xcode import XcodePlatform

import platform


class tvOSPlatform(XcodePlatform):
    def __init__(self, parameters):
        XcodePlatform.__init__(self, parameters)

    @staticmethod
    def identifier():
        return 'tvos'

    @staticmethod
    def sdk():
        return 'appletvos'

    @staticmethod
    def os_name():
        return 'tvos'

    @staticmethod
    def minimum_version():
        return '9.0'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-tvos-version', default=tvOSPlatform.minimum_version(),
                            help='the minimum tvOS version to build for')

    @staticmethod
    def detection_macro(architecture):
        return 'TARGET_OS_TV && !TARGET_OS_SIMULATOR'

    def default_architecture(self):
        return 'arm64'


class tvOSSimulatorPlatform(tvOSPlatform):
    def __init__(self, parameters):
        tvOSPlatform.__init__(self, parameters)

    @staticmethod
    def identifier():
        return 'tvossimulator'

    @staticmethod
    def sdk():
        return 'appletvsimulator'

    @staticmethod
    def add_arguments(parser):
        pass

    @staticmethod
    def detection_macro(architecture):
        return 'TARGET_OS_TV && TARGET_OS_SIMULATOR'

    def default_architecture(self):
        return platform.machine()
