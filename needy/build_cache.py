import logging
import os
import time
import json

from contextlib import contextmanager

from .cache import Cache, Manifest
from .filesystem import TempDir, dict_file


class BuildCache:
    def __init__(self, cache, lock_timeout=10, lifetime=2*7*24*60*60, gc_frequency=24*60*60):
        self.__cache = cache
        self.__lock_timeout = lock_timeout
        self.__lifetime = lifetime
        self.__gc_frequency = gc_frequency

        self.__loaded_policies = False

    def _load_policies(self):
        if not self.__loaded_policies:
            self.__loaded_policies = True
            with self.__load_cache_policies() as p:
                if 'object_lifetime' not in p:
                    p['object_lifetime'] = self.__lifetime
                if 'gc_frequency' not in p:
                    p['gc_frequency'] = self.__gc_frequency

                self.__lifetime = p['object_lifetime']
                self.__gc_frequency = p['gc_frequency']

    @staticmethod
    def manifest_key():
        return '.manifest'

    @staticmethod
    def policy_key():
        return '.policy'

    def cache(self):
        return self.__cache

    @contextmanager
    def __load_manifest(self):
        try:
            with self.__cache.lease_file(BuildCache.manifest_key(), timeout=self.__lock_timeout, create=True) as path:
                with Manifest(path) as m:
                    yield m
        except:
            logging.warn('cache unavailable: unable to load manifest')
            raise

    @contextmanager
    def __load_cache_policies(self):
        try:
            with self.__cache.lease_file(BuildCache.policy_key(), timeout=self.__lock_timeout, create=True) as path:
                with dict_file(path) as d:
                    yield d
        except:
            logging.warn('key unavailable: unable to load policies')
            raise

    def manifest(self):
        '''Returns manifest at call time. Manifest may change between calls'''
        self._load_policies()
        with self.__load_manifest() as m:
            return m

    def store_artifacts(self, directory, key):
        '''Store artifacts to key. Makes liberal use of exceptions for errors.'''
        self._load_policies()
        logging.info('Storing build artifacts in cache')
        try:
            with self.__load_manifest() as m:
                m.touch(key)
                self.__collect_garbage(m)
            with self.__cache.lease(key, create=True):
                self.__cache.store_directory(directory, key, timeout=self.__lock_timeout)
        except:
            logging.info('key unavailable: failed to store artifacts')
            raise

    def load_artifacts(self, key, directory):
        '''Loads artifacts from key. Makes liberal use of exceptions for errors.'''
        self._load_policies()
        logging.info('Loading artifacts to build directory')
        try:
            with self.__load_manifest() as m:
                m.touch(key)
                self.__collect_garbage(m)
            with self.__cache.lease(key):
                self.__cache.load_directory(key, directory, timeout=self.__lock_timeout)
        except:
            logging.warn('key unavailable: failed to load artifacts')
            raise

    def __collect_garbage(self, manifest):
        last_gc_time = manifest.metadata()['last_gc_time'] if 'last_gc_time' in manifest.metadata() else None
        if last_gc_time and last_gc_time + self.__gc_frequency > time.time():
            return

        min_time = time.time() - self.__lifetime

        total = 0

        for key in [k for k in manifest if manifest[k].use_time < min_time]:
            try:
                self.__cache.unset_key(key)
                total += 1
            except:
                pass

        if total:
            logging.info('garbage collection removed {} expired keys'.format(total))
