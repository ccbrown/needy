try:
    from exceptions import NotImplementedError
except ImportError:
    pass


class Generator:
    def __init__(self):
        pass

    @staticmethod
    def identifier():
        raise NotImplementedError('identifier')

    def generate(self, needy):
        raise NotImplementedError('generate')
