import os
import shutil

from ..source import Source


class Directory(Source):
    def __init__(self, source_directory, directory):
        Source.__init__(self)
        self.source_directory = source_directory
        self.directory = directory

    def clean(self):
        if os.path.isdir(self.directory):
            shutil.rmtree(self.directory)
        elif os.path.exists(self.directory):
            os.remove(self.directory)
        shutil.copytree(self.source_directory, self.directory, symlinks=True, ignore=shutil.ignore_patterns('.*'))
