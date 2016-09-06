#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import logging
import os
import sys

from . import commands
from .cd import cd
from .utility import DummyContextManager
from .log_formatter import LogFormatter


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

    available_commands = commands.available_commands()

    parser = argparse.ArgumentParser(description='Helps with dependencies.')

    try:
        from argcomplete.completers import DirectoriesCompleter
        parser.add_argument('-C', help='run as if invoked from this path').completer = DirectoriesCompleter()
    except ImportError:
        pass

    parser.add_argument('-v', '--verbose', action='store_true', help='produce more verbose logs')
    parser.add_argument('-q', '--quiet', action='store_true', help='suppress output')

    subparser_group = parser.add_subparsers(
        title='commands',
        description='Use \'needy <command> --help\' to get help for a specific command.',
        dest='main_command',
        metavar='command'
    )
    for name, command in available_commands.items():
        command.add_parser(subparser_group)

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    arguments = parser.parse_args(args[1:])

    if arguments.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    if arguments.quiet:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        logging.getLogger().setLevel(logging.CRITICAL + 1)

    try:
        with cd(arguments.C) if arguments.C else DummyContextManager() as f:
            return available_commands[arguments.main_command].execute(arguments)
    finally:
        logger.removeHandler(log_handler)
        logging.shutdown()
        sys.stdout = original_stdout
        sys.stderr = original_stderr

if __name__ == '__main__':
    sys.exit(main(sys.argv))
