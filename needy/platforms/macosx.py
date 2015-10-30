from .xcode import XcodePlatform

import platform

DEFAULT_MIN_MACOSX_VERSION = '10.9'


class MacOSXPlatform(XcodePlatform):

    def __init__(self, parameters):
        XcodePlatform.__init__(
            self,
            parameters,
            os_name='macosx',
            default_minimum_version=DEFAULT_MIN_MACOSX_VERSION
        )

    @staticmethod
    def identifier():
        return 'macosx'

    def default_architecture(self):
        return platform.machine()

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-macosx-version', default=DEFAULT_MIN_MACOSX_VERSION,
                            help='the minimum Mac OS X version to build for')

    @staticmethod
    def detection_macro(architecture):
        if architecture == 'x86_64':
            return 'TARGET_OS_MAC && __LP64__'
        elif architecture == 'i386':
            return 'TARGET_OS_MAC && !__LP64__'
        return None
