from ..platform import Platform

class IOSPlatform(Platform):
    def __init__(self, parameters):
        Platform.__init__(self, parameters)
        self.minimum_version = parameters.minimum_ios_version

    @staticmethod
    def identifier():
        return 'ios'

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--minimum-ios-version', default='5.0', help='the minimum iOS version to build for')

    def c_compiler(self, architecture):
        return 'xcrun -sdk iphoneos clang -arch %s -mios-version-min=%s' % (architecture, self.minimum_version)

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk iphoneos clang++ -arch %s -mios-version-min=%s' % (architecture, self.minimum_version)
