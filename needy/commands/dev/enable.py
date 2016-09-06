from ...command import Command
from ...needy import ConfiguredNeedy


class EnableCommand(Command):
    def name(self):
        return 'enable'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description='Enables dev mode for a library. Once enabled, dev mode causes a library to always be considered out-of-date, and skips the source cleaning normally done during builds.',
            help='enables dev mode for a library'
        )
        parser.add_argument('library', help='the library to enable dev mode for')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.set_development_mode(arguments.library, True)
        return 0
