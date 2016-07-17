import json
import os
import time
import shutil

from .functional_test import TestCase
from needy.filesystem import dict_file, TempDir


class DirectoryCacheTest(TestCase):
    def test_satisfy(self):
        with TempDir() as cache_dir:
            with dict_file(os.path.join(self.path(), 'needs.json')) as d:
                d['libraries'] = {
                    'lua': {
                        'download': 'http://www.lua.org/ftp/lua-5.2.1.tar.gz',
                        'checksum': '6bb1b0a39b6a5484b71a83323c690154f86b2021',
                        'project': {
                            'make-targets': 'generic',
                            'make-prefix-arg': 'INSTALL_TOP',
                        }
                    }
                }

            self.assertEqual(self.execute(['cache', 'query']), 0)
            self.assertEqual(self.execute(['cache', 'set', cache_dir]), 0)
            self.assertEqual(self.execute(['cache', 'query']), 0)
            start = time.time()
            self.assertEqual(self.execute(['satisfy', '-v']), 0)
            uncached_time = time.time() - start

            def check_output():
                self.assertTrue(os.path.isfile(os.path.join(self.build_directory('lua'), 'include', 'lua.h')))
                self.assertTrue(os.path.isfile(os.path.join(self.build_directory('lua'), 'lib', 'liblua.a')))
                self.assertTrue('lua' in os.listdir(cache_dir))
                self.assertTrue('.manifest' in os.listdir(cache_dir))
                self.assertTrue('.policy' in os.listdir(cache_dir))

                with dict_file(os.path.join(cache_dir, '.manifest')) as d:
                    self.assertGreater(len(d['keys']), 0)

            check_output()

            shutil.rmtree(self.build_directory('lua'))

            cached_start = time.time()
            self.assertEqual(self.satisfy(), 0)
            cached_time = time.time() - cached_start

            check_output()

            self.assertGreater(uncached_time, cached_time)
            self.assertLess(cached_time, 2)

            self.assertEqual(self.execute(['cache', 'unset']), 0)
