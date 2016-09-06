import textwrap

from ..command import Command
from ..needy import ConfiguredNeedy


class InitCommand(Command):
    def name(self):
        return 'init'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description=textwrap.dedent('''\
                Initializes library source directories. This means the source will be downloaded and 'cleaned'. Afterwards, it can be browsed (see
                the 'sourcedir' command) or put into dev mode (see the 'dev enable' command).
            '''),
            help='initializes library source directories'
        )
        parser.add_argument('library', default=None, nargs='*', help='the library to initialize the source of. shell-style wildcards are allowed')
        parser.add_argument('-t', '--target', default='host', help='initialize the source for this target (example: ios:armv7)')
        parser.add_argument('-D', '--define', nargs='*', action='append', help='specify a user-defined variable to be passed to the needs file renderer')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.initialize(needy.target(arguments.target), arguments.library)
        return 0
