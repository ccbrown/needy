from __future__ import print_function

from .. import command
from ..needy import ConfiguredNeedy


class SourceDirCommand(command.Command):
    def name(self):
        return 'sourcedir'

    def add_parser(self, group):
        short_description = 'gets the source directory for a need'
        parser = group.add_parser(self.name(), description=short_description.capitalize()+'.', help=short_description)
        parser.add_argument('library', help='the library to get the directory for').completer = command.library_completer

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            print(needy.source_directory(arguments.library), end='')
        return 0
