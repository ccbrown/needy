from __future__ import print_function

import argparse
import json
import os
import sys
import logging

from . import dev
from .cd import cd
from .utility import DummyContextManager
from .needy import ConfiguredNeedy
from .log_formatter import LogFormatter
from .platforms import available_platforms
from .generators import available_generators
from .caches.directory import Directory
from .needy_configuration import NeedyConfiguration


def satisfy(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s satisfy' % os.path.basename(sys.argv[0]),
        description='Satisfies library and universal binary needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('library', default=None, nargs='*', help='the library to satisfy. shell-style wildcards are allowed')
    parser.add_argument('-t', '--target', default='host', help='builds needs for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='builds the universal binary with the given name')
    parser.add_argument('-j', '--concurrency', default=1, const=0, nargs='?', type=int, help='number of jobs to process concurrently. omit or specify 0 for full concurrency')
    parser.add_argument('-f', '--force-build', action='store_true', help='force a build even when the target is up-to-date')
    parser.add_argument('-D', '--define', nargs='*', action='append', help='specify a user-defined variable to be passed to the needs file renderer')

    for platform in available_platforms().values():
        platform.add_arguments(parser)
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        if parameters.universal_binary:
            needy.satisfy_universal_binary(parameters.universal_binary, parameters.library)
        else:
            needy.satisfy_target(needy.target(parameters.target), parameters.library)

    return 0


def init(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s init' % os.path.basename(sys.argv[0]),
        description='Initializes library source directories.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('library', default=None, nargs='*', help='the library to initialize the source of. shell-style wildcards are allowed')
    parser.add_argument('-t', '--target', default='host', help='initialize the source for this target (example: ios:armv7)')
    parser.add_argument('-D', '--define', nargs='*', action='append', help='specify a user-defined variable to be passed to the needs file renderer')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        needy.initialize(needy.target(parameters.target), parameters.library)

    return 0


def cflags(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s cflags' % os.path.basename(sys.argv[0]),
        description='Gets compiler flags required for using the needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('library', default=None, nargs='*', help='the library to satisfy. shell-style wildcards are allowed')
    parser.add_argument('-t', '--target', default='host', help='gets flags for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets flags for this universal binary')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        print(' '.join([('-I%s' % path) for path in needy.include_paths(
            parameters.universal_binary if parameters.universal_binary else needy.target(parameters.target), parameters.library)]), end='')

    return 0


def ldflags(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s ldflags' % os.path.basename(sys.argv[0]),
        description='Gets linker flags required for using the needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('library', default=None, nargs='*', help='the library to satisfy. shell-style wildcards are allowed')
    parser.add_argument('-t', '--target', default='host', help='gets flags for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets flags for this universal binary')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
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
    parser.add_argument('-t', '--target', default='host', help='gets the directory for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets the directory for this universal binary')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
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

    with ConfiguredNeedy('.', parameters) as needy:
        print(needy.source_directory(parameters.library), end='')

    return 0


def generate(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s generate' % os.path.basename(sys.argv[0]),
        description='Generates useful files.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('file', default=None, nargs='+', choices=[g.identifier() for g in available_generators()], help='the file to generate')
    parser.add_argument('--satisfy-args', default='', nargs='?', help='arguments to use when satisfying needs')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        needy.generate(parameters.file)

    return 0


def dev_mode_name_change_notice(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s dev-mode' % os.path.basename(sys.argv[0]),
        description='Replaced by dev command.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('args', nargs=argparse.REMAINDER)
    parameters = parser.parse_args(args)

    logging.error('This command has been replaced. Use the dev command instead.')
    return 1


def pkg_config_path(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s pkg-config-path' % os.path.basename(sys.argv[0]),
        description='Gets the path required for using pkg-config.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('library', default=None, nargs='*', help='the library to satisfy. shell-style wildcards are allowed')
    parser.add_argument('-t', '--target', default='host', help='gets path for this target (example: ios:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets flags for this universal binary')
    parameters = parser.parse_args(args)

    with ConfiguredNeedy('.', parameters) as needy:
        print(needy.pkg_config_path(parameters.universal_binary if parameters.universal_binary else needy.target(parameters.target), parameters.library), end='')

    return 0


def main(args=sys.argv):
    try:
        import colorama
        colorama.init()
    except ImportError:
        pass

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(LogFormatter())
    logger.addHandler(log_handler)

    parser = argparse.ArgumentParser(
        description='Helps with dependencies.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""available commands:
  satisfy          satisfies libraries / universal binary needs
  init             initializes library source directories
  cflags           emits the compiler flags required to use the satisfied needs
  ldflags          emits the linker flags required to use the satisfied needs
  builddir         emits the build directory for a need
  sourcedir        emits the source directory for a need
  pkg-config-path  emits the pkg-config path for a need
  generate         generates useful files
  dev              provides tools for development of needs

Use '%s <command> --help' to get help for a specific command.
""" % os.path.basename(sys.argv[0])
    )
    parser.add_argument('command', help='see below')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    parser.add_argument('-C', help='run as if invoked from this path')
    parser.add_argument('-v', '--verbose', action='store_true', help='produce more verbose logs')
    parser.add_argument('-q', '--quiet', action='store_true', help='suppress output')
    parameters = parser.parse_args(args[1:])

    if parameters.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    commands = {
        'satisfy': satisfy,
        'init': init,
        'cflags': cflags,
        'ldflags': ldflags,
        'builddir': builddir,
        'sourcedir': sourcedir,
        'pkg-config-path': pkg_config_path,
        'generate': generate,
        'dev-mode': dev_mode_name_change_notice,
        'dev': dev.command_handler
    }

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    if parameters.quiet:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        logging.getLogger().setLevel(logging.CRITICAL + 1)

    try:
        with cd(parameters.C) if parameters.C else DummyContextManager() as f:
            if parameters.command in commands:
                return commands[parameters.command](parameters.args)
            elif parameters.command == 'help':
                if len(parameters.args) == 1 and parameters.args[0] in commands:
                    commands[parameters.args[0]](['--help'])
                else:
                    parser.print_help()
                return 1
            else:
                print('\'%s\' is not a valid command. See \'%s --help\'.' % (parameters.command, os.path.basename(sys.argv[0])))
                return 1
    finally:
        logger.removeHandler(log_handler)
        logging.shutdown()
        sys.stdout = original_stdout
        sys.stderr = original_stderr

if __name__ == '__main__':
    sys.exit(main(sys.argv))
