import os

from ..source import Source


class GitRepository(Source):
    def __init__(self, repository, commit, directory):
        Source.__init__(self)
        self.repository = repository
        self.commit = commit
        self.directory = directory

    def clean(self):
        import subprocess

        if not os.path.exists(self.directory):
            self.__fetch()

        original_directory = os.getcwd()
        os.chdir(self.directory)

        try:
            subprocess.check_call(['git', 'clean', '-xfd'])
            subprocess.check_call(['git', 'reset', '--hard', self.commit])
            subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])
        finally:
            os.chdir(original_directory)

    def __fetch(self):
        import subprocess

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        original_directory = os.getcwd()
        os.chdir(self.directory)

        try:
            if not os.path.exists(os.path.join(self.directory, '.git')):
                subprocess.check_call(['git', 'clone', self.repository, '.'])
                subprocess.check_call(['git', 'submodule', 'update', '--init', '--recursive'])
        finally:
            os.chdir(original_directory)
