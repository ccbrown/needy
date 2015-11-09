from ..platform import Platform


class XcodePlatform(Platform):
    def __init__(self, parameters):
        Platform.__init__(self, parameters)
        self.__minimum_version = self.minimum_version()
        if 'minimum_%s_version' % self.os_name().lower() in parameters:
            self.__minimum_version = getattr(parameters, 'minimum_%s_version' % self.os_name().lower())
        self.__embed_bitcode = self.identifier() in ['iphoneos', 'appletvos', 'watchos']

    @staticmethod
    def os_name():
        raise NotImplementedError('os_name')

    @staticmethod
    def minimum_version():
        raise NotImplementedError('minimum_version')

    def sdk(self):
        return 'macosx' if self.identifier() == 'host' else self.identifier()

    def __common_compiler_args(self, architecture):
        args = []
        args.append('-arch %s' % architecture)
        args.append('-m%s-version-min=%s' % (self.os_name().lower(), self.__minimum_version))
        if self.__embed_bitcode:
            args.append('-fembed-bitcode')
        return ' '.join(args)

    def c_compiler(self, architecture):
        return 'xcrun -sdk %s clang %s' % (self.sdk(), self.__common_compiler_args(architecture))

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk %s clang++ %s' % (self.sdk(), self.__common_compiler_args(architecture))
