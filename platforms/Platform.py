from exceptions import NotImplementedError

class Platform:
    def __init__(self):
        pass

    @staticmethod
    def identifier():
        raise NotImplementedError('identifier')

    def default_architecture(self):
        return None

    def c_compiler(self, architecture):
        return None

    def cxx_compiler(self, architecture):
        return None

    def required_libraries(self, architecture):
        return []