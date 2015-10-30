from .xcode import XcodePlatform

DEFAULT_MIN_TVOS_VERSION = '9.0'


class AppleTVPlatform(XcodePlatform):
    def __init__(self, parameters):
        XcodePlatform.__init__(
            self,
            parameters,
            os_name='tvos',
            default_minimum_version=DEFAULT_MIN_TVOS_VERSION
        )

    @staticmethod
    def identifier():
        return 'appletvos'

    def default_architecture(self):
        return 'arm64'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-tvos-version', default=DEFAULT_MIN_TVOS_VERSION,
                            help='the minimum tvOS version to build for')

    @staticmethod
    def detection_macro(architecture):
        return 'TARGET_OS_TV && !TARGET_OS_SIMULATOR'
