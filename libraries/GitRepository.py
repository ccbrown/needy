import os


class GitRepository:
    def __init__(self, repository, commit, directory):
        self.repository = repository
        self.commit = commit
        self.directory = directory

    def fetch(self):
        import subprocess

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        original_directory = os.getcwd()
        os.chdir(self.directory)

        try:
            if not os.path.exists(os.path.join(self.directory, '.git')):
                subprocess.check_call(['git', 'clone', self.repository, '.'])
        finally:
            os.chdir(original_directory)

    def clean(self):
        import subprocess

        if not os.path.exists(self.directory):
            self.fetch()

        original_directory = os.getcwd()
        os.chdir(self.directory)

        try:
            subprocess.check_call(['git', 'clean', '-xfd'])
            subprocess.check_call(['git', 'reset', '--hard', self.commit])
        finally:
            os.chdir(original_directory)
