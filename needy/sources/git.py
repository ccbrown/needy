import os
import logging

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
        if not os.path.exists(os.path.join(self.directory, '.git')):
            self.__fetch()

        with cd(self.directory):
            command(['git', 'clean', '-xfd'], logging.DEBUG)
            command(['git', 'fetch'], logging.DEBUG)
            command(['git', 'reset', '--hard', self.commit], logging.DEBUG)
            command(['git', 'submodule', 'update', '--init', '--recursive'], logging.DEBUG)

    def __fetch(self):
        if not os.path.exists(os.path.dirname(self.directory)):
            os.makedirs(os.path.dirname(self.directory))

        with cd(os.path.dirname(self.directory)):
            command(['git', 'clone', self.repository, os.path.basename(self.directory)], logging.DEBUG)

        with cd(self.directory):
            command(['git', 'submodule', 'update', '--init', '--recursive'], logging.DEBUG)
