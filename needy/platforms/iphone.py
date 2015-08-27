from ..platform import Platform

DEFAULT_MIN_IOS_VERSION = '5.0'


class iPhonePlatform(Platform):
    def __init__(self, parameters):
        Platform.__init__(self, parameters)
        self.__minimum_version = parameters.minimum_ios_version if 'minimum_ios_version' in parameters else DEFAULT_MIN_IOS_VERSION

    @staticmethod
    def identifier():
        return 'iphone'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-ios-version', default=DEFAULT_MIN_IOS_VERSION, help='the minimum iOS version to build for')

    def c_compiler(self, architecture):
        return 'xcrun -sdk iphoneos clang -arch %s -mios-version-min=%s' % (architecture, self.__minimum_version)

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk iphoneos clang++ -arch %s -mios-version-min=%s' % (architecture, self.__minimum_version)
