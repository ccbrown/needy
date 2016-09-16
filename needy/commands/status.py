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
        command.add_target_specification_args(parser, 'shows the status')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.show_status(arguments.universal_binary if arguments.universal_binary else needy.target(arguments.target))
        return 0
