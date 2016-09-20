import textwrap

from .. import command
from ..needy import ConfiguredNeedy


class InitCommand(command.Command):
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
        parser.add_argument('library', default=None, nargs='*', help='the library to initialize the source of. shell-style wildcards are allowed').completer = command.library_completer
        command.add_target_specification_args(parser, 'initializes the source directory', allow_universal_binary=False)

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.initialize(needy.target(arguments.target), arguments.library)
        return 0
