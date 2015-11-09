from .xcode import XcodePlatform

import platform

class OSXPlatform(XcodePlatform):
    def __init__(self, parameters):
        XcodePlatform.__init__(self, parameters)

    @staticmethod
    def identifier():
        return 'macosx'

    @staticmethod
    def os_name():
        return 'macosx'

    @staticmethod
    def minimum_version():
        return '10.9'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-macosx-version', default=OSXPlatform.minimum_version(),
                            help='the minimum OS X version to build for')

    @staticmethod
    def detection_macro(architecture):
        if architecture == 'x86_64':
            return 'TARGET_OS_MAC && __LP64__'
        elif architecture == 'i386':
            return 'TARGET_OS_MAC && !__LP64__'
        return None

    def default_architecture(self):
        return platform.machine()

