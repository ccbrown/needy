from Platform import Platform

class IOSPlatform(Platform):
    def __init__(self, minimum_version):
        Platform.__init__(self)
        self.minimum_version = minimum_version

    @staticmethod
    def identifier():
        return 'ios'

    def c_compiler(self, architecture):
        return 'xcrun -sdk iphoneos clang -arch %s -mios-version-min=%s' % (architecture, self.minimum_version)

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk iphoneos clang++ -arch %s -mios-version-min=%s' % (architecture, self.minimum_version)
