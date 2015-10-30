from ..platform import Platform


class XcodePlatform(Platform):
    def __init__(self, parameters, os_name, default_minimum_version):
        Platform.__init__(self, parameters)
        self._os_name = os_name
        self.__minimum_version = default_minimum_version
        if 'minimum_%s_version' % os_name in parameters:
            self.__minimum_version = getattr(parameters, 'minimum_%s_version' % os_name)
        self.__embed_bitcode = self.identifier() in ['iphoneos', 'appletvos', 'watchos']

    @property
    def os_name(self):
        return self._os_name

    @property
    def sdk(self):
        return 'macosx' if self.identifier() == 'host' else self.identifier()

    def __common_compiler_args(self, architecture):
        args = '-arch %s -m%s-version-min=%s' % (architecture, self.os_name.lower(), self.__minimum_version)
        if self.__embed_bitcode:
            args += ' -fembed-bitcode'
        return args

    def c_compiler(self, architecture):
        return 'xcrun -sdk %s clang %s' % (self.sdk, self.__common_compiler_args(architecture))

    def cxx_compiler(self, architecture):
        return 'xcrun -sdk %s clang++ %s' % (self.sdk, self.__common_compiler_args(architecture))
