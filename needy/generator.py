try:
    from exceptions import NotImplementedError
except ImportError:
    pass


def available_generators():
    from .generators.jamfile import JamfileGenerator
    return [JamfileGenerator]


class Generator:
    def __init__(self):
        pass

    @staticmethod
    def identifier():
        raise NotImplementedError('identifier')

    def generate(self, needy):
        raise NotImplementedError('generate')
