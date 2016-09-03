try:
    from exceptions import NotImplementedError
except ImportError:
    pass


class Source:
    def __init__(self):
        pass

    @classmethod
    def identifier(cls):
        """ should return a short, lowercase string that identifies the type """
        raise NotImplementedError('identifier')

    def status_text(self):
        """ should return short status text """
        return None

    def clean(self):
        """ should fetch (if necessary) and clean the source """
        raise NotImplementedError('clean')

    def synchronize(self):
        """ should fetch (if necessary) while preserving local modifications """
        raise NotImplementedError('synchronize')
