from __future__ import print_function

from .. import command
from ..needy import ConfiguredNeedy


class PkgConfigPathCommand(command.Command):
    def name(self):
        return 'pkg-config-path'

    def add_parser(self, group):
        short_description = 'gets the path required for using pkg-config'
        parser = group.add_parser(self.name(), description=short_description.capitalize()+'.', help=short_description)
        parser.add_argument('library', default=None, nargs='*', help='the library to satisfy. shell-style wildcards are allowed').completer = command.library_completer
        command.add_target_specification_args(parser, 'gets the path')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            print(needy.pkg_config_path(arguments.universal_binary if arguments.universal_binary else needy.target(arguments.target), arguments.library), end='')
        return 0
