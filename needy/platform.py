import sys

try:
    from exceptions import NotImplementedError
except ImportError:
    pass

_available_platforms = None


def available_platforms():
    global _available_platforms

    if _available_platforms is None:
        from .platforms.host import HostPlatform
        from .platforms.android import AndroidPlatform
        platforms = [HostPlatform, AndroidPlatform]

        if sys.platform == 'darwin':
            from .platforms.osx import OSXPlatform
            from .platforms.ios import iOSPlatform, iOSSimulatorPlatform
            from .platforms.tvos import tvOSPlatform, tvOSSimulatorPlatform
            platforms.extend([
                OSXPlatform,
                iOSPlatform,
                iOSSimulatorPlatform,
                tvOSPlatform,
                tvOSSimulatorPlatform,
            ])

        _available_platforms = {}
        for platform in platforms:
            _available_platforms[platform.identifier()] = platform

    return _available_platforms


class Platform:
    def __init__(self, parameters):
        pass

    @staticmethod
    def identifier():
        raise NotImplementedError('identifier')

    @staticmethod
    def add_arguments(parser):
        pass

    def configuration_hash(self, architecture):
        """ returns a configuration hash in hex that can be used to detemine when a rebuild is necessary """
        return None

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

    @staticmethod
    def detection_macro(architecture):
        """ returns a macro that can be used to detect whether or not this is the compiled platform + architecture """
        return None
