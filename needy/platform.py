try:
    from exceptions import NotImplementedError
except ImportError:
    pass


def available_platforms():
    from .platforms.host import HostPlatform
    from .platforms.iphone import iPhonePlatform
    from .platforms.android import AndroidPlatform
    return [HostPlatform, iPhonePlatform, AndroidPlatform]


class Platform:
    def __init__(self, parameters):
        pass

    @staticmethod
    def identifier():
        raise NotImplementedError('identifier')

    @staticmethod
    def add_arguments(parser):
        pass

    def default_architecture(self):
        """ returns the architecture to use if none is given """
        return None

    def binary_paths(self, architecture):
        """ returns paths to inject in front of PATH """
        return []

    def c_compiler(self, architecture):
        raise NotImplementedError('c_compiler')

    def cxx_compiler(self, architecture):
        raise NotImplementedError('cxx_compiler')

    def libraries(self, architecture):
        """ returns additional libraries that should be linked to """
        return []
