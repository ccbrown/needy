from .. import command
from ..generators import available_generators
from ..needy import ConfiguredNeedy


class GenerateCommand(command.Command):
    def name(self):
        return 'generate'

    def add_parser(self, group):
        short_description = 'generates useful files'
        parser = group.add_parser(self.name(), description=short_description.capitalize()+'.', help=short_description)
        parser.add_argument('file', default=None, nargs='+', choices=[g.identifier() for g in available_generators()], help='the file to generate')
        parser.add_argument('--satisfy-args', default='', nargs='?', help='arguments to use when satisfying needs')
        command.add_target_specification_args(parser, 'initializes the source directory')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.generate(arguments.file)
        return 0
