import os
import subprocess

from ..source import Source
from ..cd import cd


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
            subprocess.check_call(['git', 'clean', '-xfd'])
            subprocess.check_call(['git', 'reset', '--hard', self.commit])
            subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])

    def __fetch(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        with cd(self.directory):
            if not os.path.exists(os.path.join(self.directory, '.git')):
                subprocess.check_call(['git', 'clone', self.repository, '.'])
                subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])
