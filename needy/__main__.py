from __future__ import print_function

import argparse
import fcntl
import os
import sys

from .needy import Needy
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
        help='builds needs for this target (example: iphone:armv7)')
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

    for platform in available_platforms():
        platform.add_arguments(parser)
    parameters = parser.parse_args(args)

    needy = Needy('needs.json', parameters)

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
    parser.add_argument('-t', '--target', default='host', help='gets flags for this target (example: iphone:armv7)')
    parameters = parser.parse_args(args)

    needy = Needy('needs.json', parameters)
    target = needy.target(parameters.target)

    print(' '.join([('-I%s' % path) for path in needy.include_paths(target)]), end='')
    return 0


def ldflags(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s ldflags' % os.path.basename(sys.argv[0]),
        description='Gets linker flags required for using the needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-t', '--target', default='host', help='gets flags for this target (example: iphone:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets flags for this universal binary')
    parameters = parser.parse_args(args)

    needy = Needy('needs.json', parameters)

    print(' '.join([('-L%s' % path) for path in needy.library_paths(parameters.universal_binary if parameters.universal_binary else needy.target(parameters.target))]), end='')
    return 0

def builddir(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s builddir' % os.path.basename(sys.argv[0]),
        description='Gets the build directory for a need.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('library', help='the library to get the directory for')
    parser.add_argument('-t', '--target', default='host', help='gets the directory for this target (example: iphone:armv7)')
    parser.add_argument('-u', '--universal-binary', help='gets the directory for this universal binary')
    parameters = parser.parse_args(args)

    needy = Needy('needs.json', parameters)

    print(needy.build_directory(parameters.library, parameters.universal_binary if parameters.universal_binary else needy.target(parameters.target)), end='')
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

    needy = Needy('needs.json', parameters)
    needy.generate(parameters.file)

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
        epilog=
"""available commands:
  satisfy     satisfies libraries / universal binary needs
  cflags      emits the compiler flags required to use the satisfied needs
  ldflags     emits the linker flags required to use the satisfied needs
  builddir    emits the build directory for a need
  generate    generates useful files

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
        'generate': generate,
    }

    lock_fd = os.open('.needy_lock', os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        if parameters.command in commands:
            return commands[parameters.command](parameters.args)
        elif parameters.command == 'help':
            if len(parameters.args) == 1 and parameters.args[0] in commands:
                commands[parameters.args[0]](['--help'])
            else:
                parser.print_help()
            return 1
    finally:
        os.close(lock_fd)

    print('\'%s\' is not a valid command. See \'%s --help\'.' % (parameters.command, os.path.basename(sys.argv[0])))
    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
