from exceptions import NotImplementedError

class Platform:
    def __init__(self):
        pass

    @staticmethod
    def identifier():
        raise NotImplementedError('identifier')

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

    def required_libraries(self, architecture):
        """ returns additional libraries that should be linked to """
        return []