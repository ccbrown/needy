from exceptions import NotImplementedError

class Source:
    def __init__(self):
        pass

    def clean(self):
        """ should fetch (if necessary) and clean the source """
        raise NotImplementedError('clean')