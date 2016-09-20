from __future__ import print_function

from .. import command
from ..needy import ConfiguredNeedy


class CleanCommand(command.Command):
    def name(self):
        return 'clean'

    def add_parser(self, group):
        short_description = 'clean a need'
        parser = group.add_parser(self.name(), description=short_description.capitalize()+'.', help=short_description)
        parser.add_argument('library', default=None, nargs='*', help='the library to clean. shell-style wildcards are allowed').completer = command.library_completer
        parser.add_argument('-f', '--force', action='store_true', help='ignore warnings')
        parser.add_argument('-b', '--build-directory', action='store_true', help='only clean build directories')
        command.add_target_specification_args(parser, 'gets the directory')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            needy.clean(needy.target(arguments.target), arguments.library, only_build_directory=arguments.build_directory, force=arguments.force)
        return 0
