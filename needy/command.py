try:
    from exceptions import NotImplementedError
except ImportError:
    pass


class Command:
    def name(self):
        raise NotImplementedError('name')

    def add_parser(self, group):
        pass

    def execute(self, arguments):
        raise NotImplementedError('execute')
