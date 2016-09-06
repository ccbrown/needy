from .. import command
from ..needy import ConfiguredNeedy
from ..platforms import available_platforms


class SatisfyCommand(command.Command):
    def name(self):
        return 'satisfy'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description='Satisfies your needs. This means defined libraries or universal binaries defined in your needs file will be downloaded and built if needed.',
            help='satisfies library and universal binary needs'
        )
        parser.add_argument('library', default=None, nargs='*', help='the library to satisfy. shell-style wildcards are allowed').completer = command.library_completer
        parser.add_argument('-t', '--target', default='host', help='builds needs for this target (example: ios:armv7)').completer = command.target_completer
        parser.add_argument('-u', '--universal-binary', help='builds the universal binary with the given name').completer = command.universal_binary_completer
        parser.add_argument('-j', '--concurrency', default=1, const=0, nargs='?', type=int, help='number of jobs to process concurrently. omit or specify 0 for full concurrency')
        parser.add_argument('-f', '--force-build', action='store_true', help='force a build even when the target is up-to-date')
        parser.add_argument('-D', '--define', nargs='*', action='append', help='specify a user-defined variable to be passed to the needs file renderer')

        for platform in available_platforms().values():
            platform.add_arguments(parser)

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            if arguments.universal_binary:
                needy.satisfy_universal_binary(arguments.universal_binary, arguments.library)
            else:
                needy.satisfy_target(needy.target(arguments.target), arguments.library)
        return 0
