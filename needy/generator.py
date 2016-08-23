try:
    from exceptions import NotImplementedError
except ImportError:
    pass


def available_generators():
    from .generators.jamfile import JamfileGenerator
    from .generators.pkgconfig_jam import PkgConfigJamGenerator
    from .generators.xcconfig import XCConfigGenerator
    return [JamfileGenerator, PkgConfigJamGenerator, XCConfigGenerator]


class Generator:
    def __init__(self):
        pass

    @staticmethod
    def identifier():
        raise NotImplementedError('identifier')

    def generate(self, needy):
        raise NotImplementedError('generate')
