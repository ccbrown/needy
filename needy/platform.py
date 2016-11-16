import sys
import hashlib
import json
import logging
import binascii

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

    def configuration(self, architecture):
        """ returns a dictionary of platform configuration suitable to establish uniqueness of a platform """
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
        return {
            'c-compiler': cc,
            'cxx-compiler': cxx,
        }

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
