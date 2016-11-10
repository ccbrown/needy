import hashlib
import os
import distutils.spawn
import logging
import subprocess
import pipes

from .file_cache import FileCache
from ..process import command


class S3Cache(FileCache):
    def __init__(self, path):
        if not path.startswith('s3://'):
            raise RuntimeError('s3 cache paths must begin with s3://')
        if not distutils.spawn.find_executable('aws'):
            raise RuntimeError('The aws cli is required for the s3 cache')
        self.__path = path

    @staticmethod
    def type():
        return 's3'

    @staticmethod
    def from_dict(d):
        return S3Cache(path=d['path'])

    def description(self):
        return self.__path if self.__path else ''

    def set(self, key, source):
        command(['aws', 's3', 'cp', source, self._object_path(key)], verbosity=logging.DEBUG)
        return True

    def get(self, key, destination):
        proc = subprocess.Popen(['aws', 's3', 'cp', self._object_path(key), destination],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _, err = proc.communicate()
        if proc.returncode:
            if '(404)' in err:
                return False
            raise RuntimeError('unable to retrieve cache object {}:\n{}'.format(self._object_path(key), err))
        return True

    def _object_path(self, key):
        return os.path.join(self.__path, hashlib.sha256(key.encode()).hexdigest())
