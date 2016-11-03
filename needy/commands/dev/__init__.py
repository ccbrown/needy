import importlib

from ...command import Command


def available_commands():
    commands = [getattr(importlib.import_module(cmd[0], package=__name__), cmd[1])() for cmd in [
        ('.disable', 'DisableCommand'),
        ('.enable', 'EnableCommand'),
        ('.status', 'StatusCommand'),
        ('.render', 'RenderCommand'),
        ('.sync', 'SyncCommand'),
    ]]
    return {command.name(): command for command in commands}


class DevCommand(Command):
    def name(self):
        return 'dev'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description='Provides tools to facilitate the development of needs.',
            help='provides tools for development of needs'
        )

        subgroup = parser.add_subparsers(
            title='commands',
            description='Use \'needy dev <command> --help\' to get help for a specific command.',
            dest='dev_command',
            metavar='command'
        )
        for name, command in available_commands().items():
            command.add_parser(subgroup)

    def execute(self, arguments):
        return available_commands()[arguments.dev_command].execute(arguments)
