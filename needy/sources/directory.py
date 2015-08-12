import os

from ..source import Source


class Directory(Source):
    def __init__(self, source_directory, directory):
        Source.__init__(self)
        self.source_directory = source_directory
        self.directory = directory

    def clean(self):
        if not os.path.isdir(os.path.dirname(self.directory)):
            os.makedirs(os.path.dirname(self.directory))
        if os.path.islink(self.directory):
            os.remove(self.directory)
        os.symlink(self.source_directory, self.directory)
