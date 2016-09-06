import textwrap

from .. import command
from ..needy import ConfiguredNeedy


class StatusCommand(command.Command):
    def name(self):
        return 'status'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description=textwrap.dedent('''\
                Shows the current status of the project's needs. For needs that are in dev mode, the status of their source directory will also be shown.
            '''),
            help='shows the current status of the project\'s needs'
        )
        parser.add_argument('-t', '--target', default='host', help='shows the status for this target (example: ios:armv7)').completer = command.target_completer
        parser.add_argument('-u', '--universal-binary', help='shows the status for the universal binary with the given name').completer = command.universal_binary_completer
        parser.add_argument('-D', '--define', nargs='*', action='append', help='specify a user-defined variable to be passed to the needs file renderer')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.show_status(arguments.universal_binary if arguments.universal_binary else needy.target(arguments.target))
        return 0
