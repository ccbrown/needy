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

    def __common_compiler_args(self, architecture):
        return '-arch %s -mtvos-version-min=%s -fembed-bitcode' % (architecture, self.__minimum_version)

    def c_compiler(self, architecture):
        return 'xcrun -sdk appletvos clang %s' % self.__common_compiler_args(architecture)

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk appletvos clang++ %s' % self.__common_compiler_args(architecture)

    @staticmethod
    def detection_macro(architecture):
        return 'TARGET_OS_TV && !TARGET_OS_SIMULATOR'
