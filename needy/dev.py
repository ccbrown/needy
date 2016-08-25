from __future__ import print_function

import argparse
import os
import sys
import textwrap

from .needy import ConfiguredNeedy


def enable(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s dev enable' % os.path.basename(sys.argv[0]),
        description='Enables dev mode for a library. Once enabled, dev mode causes a library to always be considered out-of-date, and skips the source cleaning normally done during builds.'
    )
    parser.add_argument('library', help='the library to enable dev mode for')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        needy.set_development_mode(parameters.library, True)

    return 0


def disable(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s dev disable' % os.path.basename(sys.argv[0]),
        description='Disables dev mode for a library.'
    )
    parser.add_argument('library', help='the library to disable dev mode for')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        needy.set_development_mode(parameters.library, False)

    return 0


def query(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s dev query' % os.path.basename(sys.argv[0]),
        description='Exits 0 if dev mode is enabled for the given library.'
    )
    parser.add_argument('library', help='the library to enable dev mode for')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        return 0 if needy.development_mode(parameters.library) else 1

    return 0


def status(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s dev status' % os.path.basename(sys.argv[0]),
        description='Shows the status of libraries that are currently in dev mode.'
    )
    parser.add_argument('-t', '--target', default='host', help='show status for this target (example: ios:armv7)')
    parameters = parser.parse_args(args)

    rows = []
    column_count = 2
    max_column_lengths = [0] * column_count

    with ConfiguredNeedy('.', parameters) as needy:
        for name, libraries in needy.libraries(needy.target(parameters.target)).items():
            assert len(libraries) == 1
            library = libraries[0]
            if library.is_in_development_mode():
                row = (name, library.source_directory())
                rows.append(row)
                for column in range(0, column_count):
                    max_column_lengths[column] = max(max_column_lengths[column], len(row[column]))

    if rows:
        print('There {} {} librar{} in dev mode:\n'.format('are' if len(rows) > 1 else 'is', len(rows), 'ies' if len(rows) > 1 else 'y'))
        for row in rows:
            for i in range(0, column_count):
                print('  {:{}}  '.format(row[i], max_column_lengths[i]), end='')
            print('')
        print('')
    else:
        print('There are no libraries in dev mode.')

    return 0


def command_handler(args=[]):
    parser = argparse.ArgumentParser(
        description='Provides tools for development of needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""available commands:
  enable           enables dev mode for a need
  disable          disables dev mode for a need
  query            exits 0 if dev mode is enabled for a given need
  status           shows the status of needs that are in dev mode

Use '%s <command> --help' to get help for a specific command.
""" % os.path.basename(sys.argv[0])
    )
    parser.add_argument('command', help='see below')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    parameters = parser.parse_args(args)

    commands = {
        'enable': enable,
        'disable': disable,
        'query': query,
        'status': status
    }

    if parameters.command in commands:
        return commands[parameters.command](parameters.args)
    elif parameters.command == 'help':
        if len(parameters.args) == 1 and parameters.args[0] in commands:
            commands[parameters.args[0]](['--help'])
        else:
            parser.print_help()
        return 1

    print('\'%s\' is not a valid command. See \'%s dev --help\'.' % (parameters.command, os.path.basename(sys.argv[0])))
    return 1
