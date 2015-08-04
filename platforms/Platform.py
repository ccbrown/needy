from exceptions import NotImplementedError

class Platform:
    def identifier(self):
        raise NotImplementedError('identifier')

    def default_architecture(self):
        return None
