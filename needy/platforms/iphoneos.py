from .xcode import XcodePlatform

DEFAULT_MIN_IOS_VERSION = '6.0'


class iPhonePlatform(XcodePlatform):
    def __init__(self, parameters):
        XcodePlatform.__init__(
            self,
            parameters,
            os_name='ios',
            default_minimum_version=DEFAULT_MIN_IOS_VERSION
        )

    @staticmethod
    def identifier():
        return 'iphoneos'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-ios-version', default=DEFAULT_MIN_IOS_VERSION,
                            help='the minimum iOS version to build for')

    @staticmethod
    def detection_macro(architecture):
        if architecture == 'arm64':
            return 'TARGET_OS_IOS && !TARGET_OS_SIMULATOR && __LP64__'
        elif architecture == 'armv7':
            return 'TARGET_OS_IOS && !TARGET_OS_SIMULATOR && !__LP64__'
        return None
