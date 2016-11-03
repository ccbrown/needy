import textwrap

from ... import command
from ...needy import ConfiguredNeedy


class RenderCommand(command.Command):
    def name(self):
        return 'render'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description=textwrap.dedent('''\
                Display the needs file in its post-rendered state.
            '''),
            help='display a rendered needs file'
        )
        parser.add_argument('-t', '--target', default='host', help='synchronize the source for this target (example: ios:armv7)').completer = command.target_completer
        parser.add_argument('-D', '--define', nargs='*', action='append', help='specify a user-defined variable to be passed to the needs file renderer')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            print(needy.render(needy.target(arguments.target)))
        return 0
