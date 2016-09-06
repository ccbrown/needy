import textwrap

from ...command import Command
from ...needy import ConfiguredNeedy


class DisableCommand(Command):
    def name(self):
        return 'disable'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description=textwrap.dedent('''\
                Disables dev mode for a library. If you made any changes while in dev mode, the build will be considered out-of-date, and the changes
                you made will be erased.
            '''),
            help='disables dev mode for a library'
        )
        parser.add_argument('library', help='the library to disable dev mode for')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.set_development_mode(arguments.library, False)
        return 0
