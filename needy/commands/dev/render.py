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
        command.add_target_specification_args(parser, 'render needs')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            print(needy.render(needy.target(arguments.target)))
        return 0
