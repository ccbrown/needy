from ..platform import Platform

DEFAULT_MIN_TVOS_VERSION = '9.0'


class AppleTVPlatform(Platform):
    def __init__(self, parameters):
        Platform.__init__(self, parameters)
        self.__minimum_version = parameters.minimum_tvos_version if 'minimum_tvos_version' in parameters else DEFAULT_MIN_TVOS_VERSION

    @staticmethod
    def identifier():
        return 'appletv'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-tvos-version', default=DEFAULT_MIN_TVOS_VERSION, help='the minimum tvOS version to build for')

    def c_compiler(self, architecture):
        return 'xcrun -sdk appletvos clang -arch %s -mtvos-version-min=%s' % (architecture, self.__minimum_version)

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk appletvos clang++ -arch %s -mtvos-version-min=%s' % (architecture, self.__minimum_version)

    @staticmethod
    def detection_macro(architecture):
        return 'TARGET_OS_TV && !TARGET_OS_SIMULATOR'
