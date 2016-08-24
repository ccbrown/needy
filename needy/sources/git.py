import os
import logging
import distutils.spawn
import subprocess

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
            command(['git', 'clean', '-xffd'], logging.DEBUG)
            try:
                command(['git', 'fetch'], logging.DEBUG)
            except subprocess.CalledProcessError:
                # we should be okay with this to enable offline builds
                logging.warn('git fetch failed for {}'.format(self.directory))
                pass
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
