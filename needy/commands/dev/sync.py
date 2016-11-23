import textwrap

from ... import command
from ...needy import ConfiguredNeedy


class SyncCommand(command.Command):
    def name(self):
        return 'sync'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description=textwrap.dedent('''\
                Attempts to re-apply local changes to the upstream source specified in the library configuration. For example, if your have uncommitted changed
                in a Git source, this might stash them, fetch and checkout the desired upstream commit, then apply the previously stashed changes.
            '''),
            help='synchronizes upstream changes while keeping local changes'
        )
        parser.add_argument('library', nargs='*', help='a library to synchronize').completer = command.library_completer
        command.add_target_specification_args(parser, 'sync needs')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.synchronize(needy.target(arguments.target), arguments.library)
        return 0
