import os

from .. import command
from ..needy import ConfiguredNeedy


class ExecCommand(command.Command):
    def name(self):
        return 'exec'

    def add_parser(self, group):
        short_description = 'invoke a command from the source directory of a need'
        parser = group.add_parser(self.name(), description=short_description.capitalize()+'.', help=short_description)
        parser.add_argument('library', help='the library who\'s source directory will be used').completer = command.library_completer
        parser.add_argument('command', nargs='+', help='command to invoke')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            if not os.path.isdir(needy.source_directory(arguments.library)):
                raise RuntimeError('Please initialize the library before using exec.')

        os.chdir(needy.source_directory(arguments.library))
        os.execvp(arguments.command[0], arguments.command)
