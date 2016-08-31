import sys
import hashlib
import json

try:
    from exceptions import NotImplementedError
except ImportError:
    pass


class Platform:
    def __init__(self, parameters={}):
        pass

    @staticmethod
    def identifier():
        raise NotImplementedError('identifier')

    @staticmethod
    def is_host():
        return False

    @staticmethod
    def add_arguments(parser):
        pass

    def environment_overrides(self, architecture):
        return {}

    def configuration_hash(self, architecture):
        """ returns a configuration hash in hex that can be used to detemine when a rebuild is necessary """
        return None

    def configuration_hash(self, architecture):
        cc = ''
        cxx = ''

        try:
            cc = self.c_compiler(architecture)
        except NotImplementedError:
            pass
        try:
            cxx = self.cxx_compiler(architecture)
        except NotImplementedError:
            pass

        hash = hashlib.sha256()
        hash.update(json.dumps({
            'c-compiler': cc,
            'cxx-compiler': cxx,
        }, sort_keys=True).encode())
        return hash.digest()

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
