import textwrap
import logging
import json
import itertools

from .. import command
from ..needy import ConfiguredNeedy
from ..target import Target
from ..utility import log_section, dedented_unified_diff, Fore, Style
from ..universal_binary import UniversalBinary


class StatusCommand(command.Command):
    def name(self):
        return 'status'

    def add_parser(self, group):
        parser = group.add_parser(
            self.name(),
            description=textwrap.dedent('''\
                Shows the current status of the project's needs. For needs that are in dev mode, the status of their source directory will also be shown.
            '''),
            help='shows the current status of the project\'s needs'
        )
        command.add_target_specification_args(parser, 'shows the status')

    def execute(self, arguments):
        with ConfiguredNeedy('.', arguments) as needy:
            t_or_ub = arguments.universal_binary if arguments.universal_binary else needy.target(arguments.target)
            self.show_status(needy, t_or_ub)
        return 0

    @classmethod
    def show_status(cls, needy, target_or_universal_binary):
        print('Status for {}:\n'.format(target_or_universal_binary))
        libs = needy.libraries(target_or_universal_binary)
        names_to_libraries = [(k, libs[k]) for k in sorted(libs.keys())]
        names = [name for name, v in sorted(names_to_libraries)]
        statuses = []
        substatuses = []
        colors = []
        unified_diffs = []

        for name, libraries in names_to_libraries:
            if isinstance(target_or_universal_binary, Target):
                lib_or_ub = libraries[0]
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    diff = [' ' * 4 + l for l in dedented_unified_diff(
                        a=str.splitlines(json.dumps(
                            lib_or_ub.status_dict(),
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '))),
                        b=str.splitlines(json.dumps(
                            lib_or_ub.configuration_dict(),
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '))),
                        fromfile='before',
                        tofile='after',
                        lineterm='')
                    ]
                    unified_diffs.append(diff)
                else:
                    unified_diffs.append(None)
            else:
                lib_or_ub = UniversalBinary(target_or_universal_binary, libraries, needy)
                # TODO: support unified diffs for UniversalBinary targets
                unified_diffs.append(None)

            statuses.append(lib_or_ub.status_text())
            substatuses.append(lib_or_ub.substatus_texts())
            colors.append(Fore.GREEN if lib_or_ub.is_up_to_date() else Fore.RED)

        col0_content = names + list(itertools.chain(*[[k for k, v in e.items()] for e in substatuses]))
        col_widths = StatusCommand.__max_width_per_col([col0_content])
        for color, name, status, substatus, diff in zip(colors, names, statuses, substatuses, unified_diffs):
            print(color + '    {:{}}{}'.format(name, col_widths[0] + 6, status) + Fore.RESET)
            for key, value in substatus.items():
                print((Style.DIM + '      {:{}}{}' + Style.RESET_ALL).format(key, col_widths[0] + 4, value))
            if logging.getLogger().isEnabledFor(logging.DEBUG) and diff:
                for l in diff:
                    logging.debug(Style.DIM + l + Style.RESET_ALL)
        print('')

    @classmethod
    def __max_width_per_col(cls, cols):
        return list([len(max(list(x), key=len)) for x in cols])
