import argparse
import os
import sys

from .needy import Needy
from .platform import available_platforms


def satisfy(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s satisfy' % os.path.basename(sys.argv[0]),
        description='Satisfies library and universal binary needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
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
    for platform in available_platforms():
        platform.add_arguments(parser)
    parameters = parser.parse_args(args)

    needy = Needy(os.path.abspath('needs.json'), parameters)

    if parameters.universal_binary:
        needy.satisfy_universal_binary(parameters.universal_binary)
    else:
        needy.satisfy_target(needy.target(parameters.target))

    return 0


def cflags(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s cflags' % os.path.basename(sys.argv[0]),
        description='Gets compiler flags required for using the needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--target', default='host', help='gets flags for this target (example: ios:armv7)')
    parameters = parser.parse_args(args)

    needy = Needy(os.path.abspath('needs.json'), parameters)
    target = needy.target(parameters.target)

    print(' '.join([('-I%s' % path) for path in needy.include_paths(target)]))
    return 0


def ldflags(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s ldflags' % os.path.basename(sys.argv[0]),
        description='Gets linker flags required for using the needs.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--target', default='host', help='gets flags for this target (example: ios:armv7)')
    parameters = parser.parse_args(args)

    needy = Needy(os.path.abspath('needs.json'), parameters)
    target = needy.target(parameters.target)

    print(' '.join([('-L%s' % path) for path in needy.library_paths(target)]))
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

Use '%s <command> --help' to get help for a specific command.
""" % os.path.basename(sys.argv[0])
    )
    parser.add_argument('command', help='see below')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    parameters = parser.parse_args(args[1:])

    if parameters.command == 'satisfy':
        return satisfy(parameters.args)
    if parameters.command == 'cflags':
        return cflags(parameters.args)
    if parameters.command == 'ldflags':
        return ldflags(parameters.args)

    print('\'%s\' is not a valid command. See \'%s --help\'.' % (parameters.command, os.path.basename(sys.argv[0])))
    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
