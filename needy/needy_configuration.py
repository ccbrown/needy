import os
import json
import logging
import time

from .caches.directory import Directory
from .build_cache import BuildCache
from .filesystem import os_file, lock_fd

from contextlib import contextmanager


class NeedyConfiguration:
    def __init__(self, base_path):
        self.__base_path = base_path

        with self.__locked_needyconfig(self.__base_path) as fds:
            self.__configuration = self._evaluate_needyconfigs(fds)

    @staticmethod
    @contextmanager
    def __locked_needyconfig(base_path):
        candidates = NeedyConfiguration.__get_candidate_paths(base_path)

        if not candidates:
            yield []
            return

        lock_path, fd = NeedyConfiguration.__lock_config()

        yield [c for c in candidates if os.path.exists(c)]

        os.close(fd)
        os.remove(lock_path)

    @staticmethod
    def __get_candidate_paths(base_path):
        ''' return possible needyconfig paths from base_path to root '''
        candidates = []
        path = base_path
        while path:
            needyconfig = os.path.join(path, '.needyconfig')
            candidates.append(needyconfig)
            if path == os.path.dirname(path):
                break
            path = os.path.dirname(path)
        return candidates

    @staticmethod
    def __lock_config():
        lock_path = os.path.join(os.path.expanduser('~'), '.needyconfig.lock')
        fd = None
        start = time.time()
        while time.time() < start + 10:
            try:
                fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                break
            except OSError:
                try:
                    time.sleep(0.1)
                    continue
                except:
                    break
        if not fd:
            raise RuntimeError('Unable to lock {}, if there are no other needy instances running, delete this manually and try again'.format(lock_path))
        return lock_path, fd

    @staticmethod
    def _recursive_merge(a, b):
        ''' lists in b appending to lists in a and keys in b adding to keys in a '''
        if isinstance(a, list):
            a.extend(b)
        else:
            for k in a:
                if k in b:
                    if isinstance(a[k], list):
                        a[k].extend(b[k])
                    elif isinstance(a[k], dict):
                        NeedyConfiguration._recursive_merge(a[k], b[k])
                    else:
                        a[k] = b[k]
                else:
                    a[k] = b[k]

    @staticmethod
    def _evaluate_needyconfigs(paths):
        config = dict()
        for p in paths:
            with open(p, 'r') as f:
                content = f.read()
                parent_config = json.loads(content) if content else dict()
                for k in parent_config:
                    if k in config:
                        NeedyConfiguration._recursive_merge(config[k], parent_config[k])
                    else:
                        config[k] = parent_config[k]

        return config

    def build_caches(self):
        build_caches = []
        if 'build-caches' in self.__configuration:
            if isinstance(self.__configuration['build-caches'], list):
                build_caches = self.__configuration['build-caches']
            else:
                build_caches = [self.__configuration['build-caches']]
        return [BuildCache(Directory.from_dict(c)) for c in [c if isinstance(c, dict) else {'path': c} for c in build_caches]]
