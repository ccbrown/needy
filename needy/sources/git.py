import os
import logging
import distutils

from ..source import Source
from ..cd import cd
from ..process import command


class GitRepository(Source):
    def __init__(self, repository, commit, directory):
        Source.__init__(self)
        self.repository = repository
        self.commit = commit
        self.directory = directory

    def clean(self):
        GitRepository.__assert_git_availability()

        if not os.path.exists(os.path.join(self.directory, '.git')):
            self.__fetch()

        with cd(self.directory):
            # intentionally use 'git' instead of find_executable. Repos with './git' shouldn't fail to clean.
            command(['git', 'clean', '-xffd'], logging.DEBUG)
            command(['git', 'fetch'], logging.DEBUG)
            command(['git', 'reset', 'HEAD', '--hard'], logging.DEBUG)
            command(['git', 'checkout', '--force', self.commit], logging.DEBUG)
            command(['git', 'submodule', 'update', '--init', '--recursive'], logging.DEBUG)

    def __fetch(self):
        GitRepository.__assert_git_availability()

        if not os.path.exists(os.path.dirname(self.directory)):
            os.makedirs(os.path.dirname(self.directory))

        with cd(os.path.dirname(self.directory)):
            command(['git', 'clone', self.repository, os.path.basename(self.directory)], logging.DEBUG)

        with cd(self.directory):
            command(['git', 'submodule', 'update', '--init', '--recursive'], logging.DEBUG)

    @classmethod
    def __assert_git_availability(cls):
        if not distutils.spawn.find_executable('git'):
            raise RuntimeError('No git binary is present')
