from __future__ import print_function

import argparse
import json
import os
import sys
import logging

from .needy import Needy
from .local_configuration import LocalConfiguration
from .platform import available_platforms
from .generator import available_generators


def satisfy(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s satisfy' % os.path.basename(sys.argv[0]),
        description='Satisfies library and universal binary needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'library',
        default=None,
        nargs='*',
        help='the library to satisfy. shell-style wildcards are allowed')
    parser.add_argument(
        '-t', '--target',
        default='host',
        help='builds needs for this target (example: ios:armv7)')
    parser.add_argument(
        '-u', '--universal-binary',
        help='builds the universal binary with the given name')
    parser.add_argument(
        '-j', '--concurrency',
        default=1,
        const=0,
        nargs='?',
        type=int,
        help='number of jobs to process concurrently')
    parser.add_argument(
        '-f', '--force-build',
        action='store_true',
        help='force a build even when the target is up-to-date')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='produce more verbose logs')
    parser.add_argument(
        '-D', '--define',
        nargs='*',
        action='append',
        help='specify a user-defined variable to be passed to the needs file renderer')

    for platform in available_platforms().values():
        platform.add_arguments(parser)
    parameters = parser.parse_args(args)

    logging.basicConfig(format=('%(message)s'), level=logging.DEBUG if parameters.verbose else logging.INFO)

    with LocalConfiguration(os.path.join(Needy.resolve_needs_directory('.'), 'config.json')) as local_configuration:
        needy = Needy('.', parameters, local_configuration=local_configuration)
        if parameters.universal_binary:
            needy.satisfy_universal_binary(parameters.universal_binary, parameters.library)
        else:
            needy.satisfy_target(needy.target(parameters.target), parameters.library)

    return 0


def cflags(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s cflags' % os.path.basename(sys.argv[0]),
        description='Gets compiler flags required for using the needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'library',
        default=None,
        nargs='*',
        help='the library to satisfy. shell-style wildcards are allowed')
    parser.add_argument('-t', '--target', default='host', help='gets flags for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets flags for this universal binary')
    parameters = parser.parse_args(args)

    with LocalConfiguration(os.path.join(Needy.resolve_needs_directory('.'), 'config.json')) as local_configuration:
        needy = Needy('.', parameters, local_configuration=local_configuration)
        print(' '.join([('-I%s' % path) for path in needy.include_paths(
            parameters.universal_binary if parameters.universal_binary else needy.target(parameters.target), parameters.library)]), end='')

    return 0


def ldflags(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s ldflags' % os.path.basename(sys.argv[0]),
        description='Gets linker flags required for using the needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'library',
        default=None,
        nargs='*',
        help='the library to satisfy. shell-style wildcards are allowed')
    parser.add_argument('-t', '--target', default='host', help='gets flags for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets flags for this universal binary')
    parameters = parser.parse_args(args)

    with LocalConfiguration(os.path.join(Needy.resolve_needs_directory('.'), 'config.json')) as local_configuration:
        needy = Needy('.', parameters, local_configuration=local_configuration)
        print(' '.join([('-L%s' % path) for path in needy.library_paths(
            parameters.universal_binary if parameters.universal_binary else needy.target(parameters.target), parameters.library)]), end='')

    return 0


def builddir(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s builddir' % os.path.basename(sys.argv[0]),
        description='Gets the build directory for a need.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('library', help='the library to get the directory for')
    parser.add_argument(
        '-t', '--target', default='host', help='gets the directory for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets the directory for this universal binary')
    parameters = parser.parse_args(args)

    with LocalConfiguration(os.path.join(Needy.resolve_needs_directory('.'), 'config.json')) as local_configuration:
        needy = Needy('.', parameters, local_configuration=local_configuration)
        print(needy.build_directory(parameters.library,
                                    parameters.universal_binary if parameters.universal_binary else needy.target(parameters.target)), end='')

    return 0


def sourcedir(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s sourcedir' % os.path.basename(sys.argv[0]),
        description='Gets the source directory for a need.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('library', help='the library to get the directory for')
    parameters = parser.parse_args(args)

    with LocalConfiguration(os.path.join(Needy.resolve_needs_directory('.'), 'config.json')) as local_configuration:
        needy = Needy('.', parameters, local_configuration=local_configuration)
        print(needy.source_directory(parameters.library), end='')

    return 0


def generate(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s generate' % os.path.basename(sys.argv[0]),
        description='Generates useful files.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'file',
        default=None,
        nargs='+',
        choices=[g.identifier() for g in available_generators()],
        help='the file to generate')
    parser.add_argument(
        '--satisfy-args',
        default='',
        nargs='?',
        help='arguments to use when satisfying needs')
    parameters = parser.parse_args(args)

    with LocalConfiguration(os.path.join(Needy.resolve_needs_directory('.'), 'config.json')) as local_configuration:
        needy = Needy('.', parameters, local_configuration=local_configuration)
        needy.generate(parameters.file)

    return 0


def development_mode(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s dev-mode' % os.path.basename(sys.argv[0]),
        description='Enables development mode for a library.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'library',
        help='the library to enable dev mode for')
    parser.add_argument(
        '--disable',
        default=False,
        action='store_true',
        help='disables dev mode for the library')
    parser.add_argument(
        '--query',
        default=False,
        action='store_true',
        help='if given, will return 0 if dev-mode is enabled, or 1 otherwise')
    parameters = parser.parse_args(args)

    with LocalConfiguration(os.path.join(Needy.resolve_needs_directory('.'), 'config.json')) as local_configuration:
        needy = Needy('.', parameters, local_configuration=local_configuration)
        if parameters.query:
            return 0 if needy.development_mode(parameters.library) else 1
        needy.set_development_mode(parameters.library, not parameters.disable)

    return 0


def pkg_config_path(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s pkg-config-path' % os.path.basename(sys.argv[0]),
        description='Gets the path required for using pkg-config.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'library',
        default=None,
        nargs='*',
        help='the library to satisfy. shell-style wildcards are allowed')
    parser.add_argument('-t', '--target', default='host', help='gets path for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets flags for this universal binary')
    parameters = parser.parse_args(args)

    with LocalConfiguration(os.path.join(Needy.resolve_needs_directory('.'), 'config.json')) as local_configuration:
        needy = Needy('.', parameters, local_configuration=local_configuration)
        print(needy.pkg_config_path(parameters.universal_binary if parameters.universal_binary else needy.target(parameters.target), parameters.library), end='')

    return 0


def main(args=sys.argv):
    try:
        import colorama
        colorama.init()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(
        description='Helps with dependencies.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""available commands:
  satisfy     satisfies libraries / universal binary needs
  cflags      emits the compiler flags required to use the satisfied needs
  ldflags     emits the linker flags required to use the satisfied needs
  builddir    emits the build directory for a need
  sourcedir   emits the source directory for a need
  generate    generates useful files
  dev-mode    enables development mode for a library

Use '%s <command> --help' to get help for a specific command.
""" % os.path.basename(sys.argv[0])
    )
    parser.add_argument('command', help='see below')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    parameters = parser.parse_args(args[1:])

    commands = {
        'satisfy': satisfy,
        'cflags': cflags,
        'ldflags': ldflags,
        'builddir': builddir,
        'sourcedir': sourcedir,
        'generate': generate,
        'dev-mode': development_mode,
        'pkg-config-path': pkg_config_path,
    }

    try:
        if parameters.command in commands:
            return commands[parameters.command](parameters.args)
        elif parameters.command == 'help':
            if len(parameters.args) == 1 and parameters.args[0] in commands:
                commands[parameters.args[0]](['--help'])
            else:
                parser.print_help()
            return 1
    finally:
        logging.shutdown()

    print('\'%s\' is not a valid command. See \'%s --help\'.' % (parameters.command, os.path.basename(sys.argv[0])))
    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
