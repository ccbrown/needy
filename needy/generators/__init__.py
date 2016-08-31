from .jamfile import JamfileGenerator
from .pkgconfig_jam import PkgConfigJamGenerator
from .xcconfig import XCConfigGenerator


def available_generators():
    return [JamfileGenerator, PkgConfigJamGenerator, XCConfigGenerator]
