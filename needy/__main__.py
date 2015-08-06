import argparse
import colorama
import os
import sys

from needy import Needy
from platform import available_platforms
from target import Target

def satisfy(args=[]):
    parser = argparse.ArgumentParser(
        prog='%s satisfy' % os.path.basename(sys.argv[0]),
        description='Satisfies library and universal binary needs.',
        formatter_class = argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--target', default='host', help='builds needs for this target (example: ios:armv7)')
    parser.add_argument('--universal-binary', help='builds the universal binary with the given name')
    for platform in available_platforms():
        platform.add_arguments(parser)
    parameters = parser.parse_args(args)

    needy = Needy(os.path.abspath('needs.json'), parameters)

    print 'Satisfying needs for: %s' % needy.path
    print 'Needs directory: %s' % needy.needs_directory

    if parameters.target or parameters.universal_binary == None:
        parts = parameters.target.split(':')
        platform = needy.platform(parts[0])
        target = Target(platform, parts[1] if len(parts) > 1 else platform.default_architecture())
        needy.satisfy_target(target)

    if parameters.universal_binary:
        needy.satisfy_universal_binary(parameters.universal_binary)
    
    return 0

def main(args=sys.argv):
    parser = argparse.ArgumentParser(
        description='Helps with dependencies.',
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog =
"""available commands:
  satisfy     satisfies libraries / universal binary needs

Use '%s <command> --help' to get help for a specific command.
""" % os.path.basename(sys.argv[0])
    )
    parser.add_argument('command', help='see below')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    parameters = parser.parse_args(args[1:])

    if parameters.command == 'satisfy':
        return satisfy(parameters.args)

    print '\'%s\' is not a valid command. See \'%s --help\'.' % (parameters.command, os.path.basename(sys.argv[0]))
    return 1

if __name__ == "__main__":
    colorama.init()
    sys.exit(main(sys.argv))
