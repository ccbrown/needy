import distutils
import os
import re
import logging

from .. import project


# TODO: This really should be part of the MakeProject class, but
#       other build systems still use some of the MakeProject
#       arguments and parameters such as AutotoolsProject.
def get_make_jobs_args(project):
    concurrency = project.build_concurrency()

    if concurrency > 1:
        return ['-j', str(concurrency)]
    elif concurrency == 0:
        return ['-j']
    return []


class MakeProject(project.Project):

    @staticmethod
    def identifier():
        return 'make'

    @staticmethod
    def is_valid_project(definition, needy):
        return MakeProject.get_makefile_path(definition.directory) is not None

    @staticmethod
    def missing_prerequisites(definition, needy):
        return ['make'] if distutils.spawn.find_executable('make') is None else []

    @staticmethod
    def get_makefile_path(directory='.'):
        valid_makefile_names = ['Makefile', 'GNUmakefile']

        for makefile in valid_makefile_names:
            path = os.path.join(directory, makefile)
            if os.path.isfile(path):
                return path
        return None

    @staticmethod
    def configuration_keys():
        return project.Project.configuration_keys() | {'make-prefix-arg', 'make-targets'}

    def configure(self, output_directory):
        excluded_targets = []

        if not self.target().platform.is_host():
            excluded_targets.extend(['test', 'tests', 'check'])

        makefile_path = MakeProject.get_makefile_path()

        with open(makefile_path, 'r') as makefile:
            with open('MakefileNeedyGenerated', 'w') as needy_makefile:
                for line in makefile.readlines():
                    uname_assignment = re.match('(.+=).*shell .*uname', line, re.MULTILINE)
                    if uname_assignment and self.target().platform.identifier() == 'android':
                        needy_makefile.write('%sLinux\n' % uname_assignment.group(1))
                        continue

                    excluded_target = None
                    for target in excluded_targets:
                        if line.find('%s:' % target) == 0:
                            excluded_target = target
                            break

                    if excluded_target:
                        needy_makefile.write('%s:\nneedy-excluded-%s-for-non-host-platform:\n' % (excluded_target, excluded_target))
                        continue

                    needy_makefile.write(line)

    def build(self, output_directory):
        make_args = get_make_jobs_args(self)
        make_args.extend(['-f', './MakefileNeedyGenerated'])

        target_os = None

        if self.target().platform.identifier() == 'android':
            target_os = 'Linux'

        if target_os:
            make_args.extend([
                'OS=%s' % target_os,
                'TARGET_OS=%s' % target_os
            ])

        self.command(['make'] + self.__make_targets() + make_args)
        make_args.extend(self.__make_prefix_args(make_args, output_directory))
        self.command(['make', 'install'] + make_args)

    def __make_targets(self):
        return self.evaluate(self.configuration('make-targets') or [])

    def __make_prefix_args(self, other_args, output_directory):
        if self.configuration('make-prefix-arg') is not None:
            return ['%s=%s' % (self.configuration('make-prefix-arg'), output_directory)]

        args = [
            'PREFIX=%s' % output_directory,
            'INSTALLPREFIX=%s' % output_directory,
            'INSTALL_PREFIX=%s' % output_directory
        ]

        recon_args = ['make', 'install', '--recon'] + other_args + args
        recon = self.command_output(recon_args, logging.DEBUG)

        if recon.find(output_directory) < 0:
            raise RuntimeError('unable to figure out how to set installation prefix')

        return args
