import json
import os
import time
import shutil
import unittest

from .functional_test import TestCase
from needy.filesystem import dict_file, TempDir


class DirectoryCacheTest(TestCase):
    def check_output(self, lib_name, cache_dir):
        self.assertTrue(os.path.isfile(os.path.join(self.build_directory(lib_name), 'include', 'lua.h')))
        self.assertTrue(os.path.isfile(os.path.join(self.build_directory(lib_name), 'lib', 'liblua.a')))
        self.assertTrue(lib_name in os.listdir(cache_dir))
        self.assertTrue('.manifest' in os.listdir(cache_dir))
        with dict_file(os.path.join(cache_dir, '.manifest')) as d:
            self.assertGreater(len(d['keys']), 0)

    def build_to_cache(self, lib_name, cache_dir):
        with open(os.path.join(self.path(), '.needyconfig'), 'w') as f:
            f.write(json.dumps({
                'build-caches': [
                    cache_dir
                ]
            }))

        start = time.time()
        self.assertEqual(self.execute(['satisfy', '-v', lib_name]), 0)
        uncached_time = time.time() - start

        self.check_output(lib_name, cache_dir)

        return uncached_time

    def test_satisfy(self):
        with dict_file(os.path.join(self.path(), 'needs.json')) as d:
            d['libraries'] = {
                'foo': {
                    'download': 'http://www.lua.org/ftp/lua-5.2.1.tar.gz',
                    'checksum': '6bb1b0a39b6a5484b71a83323c690154f86b2021',
                    'project': {
                        'post-clean': 'echo foo',
                        'make-targets': 'generic',
                        'make-prefix-arg': 'INSTALL_TOP',
                    }
                },
                'bar': {
                    'download': 'http://www.lua.org/ftp/lua-5.2.1.tar.gz',
                    'checksum': '6bb1b0a39b6a5484b71a83323c690154f86b2021',
                    'project': {
                        'post-clean': 'echo bar',
                        'make-targets': 'generic',
                        'make-prefix-arg': 'INSTALL_TOP',
                    }
                }
            }

        with TempDir() as primary_cache, TempDir() as secondary_cache:

            uncached_time = self.build_to_cache('foo', primary_cache)
            uncached_time += self.build_to_cache('bar', secondary_cache)

            with open(os.path.join(self.path(), '.needyconfig'), 'w') as f:
                f.write(json.dumps({
                    'build-caches': [
                        primary_cache,
                        os.path.relpath(secondary_cache, os.path.dirname(f.name)),
                    ]
                }))

            shutil.rmtree(self.build_directory('foo'))
            shutil.rmtree(self.build_directory('bar'))

            cached_start = time.time()
            self.assertEqual(self.satisfy(), 0)
            cached_time = time.time() - cached_start

            self.check_output('foo', primary_cache)
            self.check_output('bar', secondary_cache)

            self.assertGreater(uncached_time, cached_time)
            self.assertLess(cached_time, 2)
