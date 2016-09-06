from __future__ import print_function

import logging
import os
import textwrap

from ... import command
from ...needy import ConfiguredNeedy


class StatusCommand(command.Command):
    def name(self):
        return 'status'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description=textwrap.dedent('''\
                With no arguments, lists the libraries that are currently in dev mode. If a library name is given, displays
                whether or not that library is in dev mode. The exit code will be non-zero if no library is indicated to be
                in dev mode.
            '''),
            help='shows the status of libraries that are in dev mode'
        )
        parser.add_argument('library', nargs='?', help='a library to check the status of').completer = command.library_completer

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            library_names = needy.development_mode_libraries()
            if arguments.library:
                if arguments.library in library_names:
                    logging.info('{} is in dev mode: {}'.format(arguments.library, os.path.relpath(needy.need_directory(arguments.library))))
                    return 0
                else:
                    logging.info('{} is not in dev mode.'.format(arguments.library))
                    return 1

            if library_names:
                print('There {} {} librar{} in dev mode:'.format(
                    'are' if len(library_names) > 1 else 'is',
                    len(library_names),
                    'ies' if len(library_names) > 1 else 'y')
                )

                print('')
                max_name_length = max([len(name) for name in library_names])
                for name in library_names:
                    print('    {}{:{}}{}'.format(name, '', max_name_length - len(name) + 4, os.path.relpath(needy.need_directory(name))))
                print('')

                return 0

        print('There are no libraries in dev mode.')
        return 1
