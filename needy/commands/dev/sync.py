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
        parser.add_argument('-t', '--target', default='host', help='synchronize the source for this target (example: ios:armv7)').completer = command.target_completer
        parser.add_argument('-D', '--define', nargs='*', action='append', help='specify a user-defined variable to be passed to the needs file renderer')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.synchronize(needy.target(arguments.target), arguments.library)
        return 0
