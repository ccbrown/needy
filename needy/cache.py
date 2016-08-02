import os
import shutil
import tarfile
import json
import logging
import time

from contextlib import contextmanager

from .filesystem import TempDir


class CacheError(Exception):
    pass


class KeyLocked(CacheError):
    '''Raised when an action would read or modify a key that is locked'''
    pass


class SourceNotFound(CacheError):
    '''Raised when a source is required to exist and isn't found'''
    pass


class KeyNotFound(CacheError):
    '''Raised when a key is required to exist and isn't found'''
    pass


class Cache:
    '''If concurrency for load and store methods is desired, utilize the
    lock_key and unlock_key methods.'''

    @staticmethod
    def type():
        '''type of cache'''
        raise NotImplementedError('type')

    def description(self):
        '''uri, path, or other configuration description'''
        raise NotImplementedError('description')

    def to_dict(self):
        '''export self to dictionary for serialization'''
        raise NotImplementedError('to_dict')

    @staticmethod
    def from_dict(d):
        '''inverse of to_dict. Should return a cache.'''
        raise NotImplementedError('from_dict')

    def store_directory(self, source, key, timeout=0):
        '''make directory at source retrievable with the key'''
        if not os.path.exists(source):
            raise SourceNotFound(source)
        with TempDir() as temp_dir:
            temp_tar = os.path.join(temp_dir, 'temp')
            tar = tarfile.open(temp_tar, 'w:gz')
            tar.add(source, arcname='.')
            tar.close()
            self.store_file(temp_tar, key, timeout)

    def load_directory(self, key, destination, timeout=0):
        '''restore directory at key to destination'''
        with TempDir() as temp_dir:
            temp_tar = os.path.join(temp_dir, key)
            self.load_file(key, temp_tar, timeout)
            tar = tarfile.open(temp_tar, 'r:gz')
            tar.extractall(path=destination)
            tar.close()

    def store_file(self, source, key, timeout=0):
        '''make file at source retrievable with key.'''
        raise NotImplementedError('store_file')

    def load_file(self, key, destination, timeout=0):
        '''restore file at key to destination'''
        raise NotImplementedError('load_file')

    def exists(self, key, timeout=0):
        '''return true if artifacts at key exist'''
        raise NotImplementedError('exists')

    def lock_key(self, key, timeout=None, create=False):
        '''lock key for exclusive use'''
        raise NotImplementedError('lock_key')

    def unlock_key(self, key):
        '''unlock key for others to use'''
        raise NotImplementedError('unlock_key')

    def unset_key(self, key):
        '''remove key from the cache'''
        raise NotImplementedError('unset_key')

    class Lease:
        def __init__(self, cache, key, **kwargs):
            self.__cache = cache
            self.__key = key
            self.__kwargs = kwargs

        def __enter__(self):
            self.__cache.lock_key(self.__key, **self.__kwargs)

        def __exit__(self, etype, value, traceback):
            self.__cache.unlock_key(self.__key)

    def lease(self, key, **kwargs):
        '''convenience wrapper around lock_key and unlock_key'''
        return Cache.Lease(self, key, **kwargs)

    @contextmanager
    def lease_file(self, key, timeout=None, **kwargs):
        '''convenience wrapper around lease a key, load a file to a temporary
        directory, and then save modifications when the lease is returned. If
        the path is removed during the lease, the key will be unset.'''
        with self.lease(key, timeout=timeout, **kwargs):
            with TempDir() as temp_dir:
                temp_file = os.path.join(temp_dir, 'f')
                self.load_file(key, temp_file, timeout=timeout)
                yield temp_file
                if os.path.exists(temp_file):
                    self.store_file(temp_file, key, timeout=timeout)
                else:
                    self.unset_key(temp_file)


class Manifest:
    def __init__(self, path):
        self.__path = path
        self.__entries = dict()

    class Entry:
        def __init__(self, d=dict()):
            self.use_time = int(d['use_time']) if 'use_time' in d else 0

        def to_dict(self):
            return {'use_time': self.use_time} if self.use_time > 0 else dict()

    def __enter__(self):
        with open(self.__path, 'r') as f:
            contents = f.read()
            d = (json.loads(contents) if contents else dict())
            self.__metadata = {k: v for k, v in d['metadata'].items()} if 'metadata' in d else dict()
            self.__entries = {k: Manifest.Entry(v) for k, v in d['keys'].items()} if 'keys' in d else dict()
        return self

    def __exit__(self, etype, value, traceback):
        try:
            with open(self.__path, 'w') as f:
                d = dict()
                if self.__metadata:
                    d['metadata'] = self.__metadata
                d['keys'] = {k: v.to_dict() for k, v in self.__entries.items()}
                json.dump(d, f)
        except:
            logging.error('error storing manifest')
            raise

    def metadata(self):
        return self.__metadata

    def touch(self, key):
        self.__entries[key] = Manifest.Entry({'use_time': int(time.time())})

    def __delitem__(self, key):
        del self.__entries[key]

    def __contains__(self, key):
        return self.__entries.__contains__(key)

    def __getitem__(self, key):
        return self.__entries.__getitem__(key)

    def __iter__(self):
        return self.__entries.__iter__()
