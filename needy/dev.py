from __future__ import print_function

import argparse
import logging
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


def status(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s dev status' % os.path.basename(sys.argv[0]),
        description='Shows the status of libraries that are currently in dev mode.'
    )
    parser.add_argument('library', nargs='?', help='a library to check the status of')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        library_names = needy.development_mode_libraries()
        if parameters.library:
            if parameters.library in library_names:
                logging.info('{} is in dev mode: {}'.format(parameters.library, needy.need_directory(parameters.library)))
                return 0
            else:
                logging.info('{} is not in dev mode.'.format(parameters.library))
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
                print('    {}{:{}}{}'.format(name, '', max_name_length - len(name) + 4, needy.need_directory(name)))
            print('')

            return 0

    print('There are no libraries in dev mode.')
    return 1


def sync(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s dev sync' % os.path.basename(sys.argv[0]),
        description='Synchronizes upstream changes while keeping local changes.'
    )
    parser.add_argument('library', nargs='*', help='a library to synchronize')
    parser.add_argument('-t', '--target', default='host', help='synchronize the source for this target (example: ios:armv7)')
    parser.add_argument('-D', '--define', nargs='*', action='append', help='specify a user-defined variable to be passed to the needs file renderer')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        needy.synchronize(needy.target(parameters.target), parameters.library)

    return 0


def command_handler(args=[]):
    parser = argparse.ArgumentParser(
        description='Provides tools for development of needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""available commands:
  enable           enables dev mode for a need
  disable          disables dev mode for a need
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
        'status': status,
        'sync': sync,
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
