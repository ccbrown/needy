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
        parser.add_argument('-t', '--target', default='host', help='gets path for this target (example: ios:armv7)').completer = command.target_completer
        parser.add_argument('-u', '--universal-binary', help='gets flags for this universal binary').completer = command.universal_binary_completer

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            print(needy.pkg_config_path(arguments.universal_binary if arguments.universal_binary else needy.target(arguments.target), arguments.library), end='')
        return 0
