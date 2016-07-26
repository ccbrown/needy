import os
import shutil

from .functional_test import TestCase
from needy.filesystem import dict_file, TempDir
from needy.cd import cd

class DirectorySource(TestCase):

    def prepare_needs(self, prefix):
        foo_include = os.path.join(prefix, 'foo', 'include')

        os.mkdir(os.path.join(prefix, 'foo'))
        os.mkdir(os.path.join(prefix, 'foo', 'include'))

        with open(os.path.join(foo_include, 'test.h'), 'w') as f:
            f.write('struct foo {};')

        with dict_file(os.path.join(self.path(), 'needs.json')) as d:
            d['libraries'] = {
                'foo': {
                    'directory': os.path.join(prefix, 'foo')
                }
            }

    def do_build(self):
        self.assertEqual(self.satisfy(), 0)

        test_h = os.path.join(self.build_directory('foo'), 'include', 'test.h')

        self.assertTrue(os.path.isfile(test_h))
        with open(test_h, 'r') as f:
            self.assertEqual(f.read(), 'struct foo {};')

    def do_clean_and_build(self):
        self.do_build()
        shutil.rmtree(self.build_directory('foo'))
        self.do_build()

    def test_absolute_path(self):
        prefix = os.path.join(self.path(), 'abs')
        os.mkdir(prefix)
        self.prepare_needs(prefix)
        self.do_clean_and_build()

    def test_relative_path(self):
        with cd(self.path()):
            os.mkdir('rel')
            self.prepare_needs('rel')
            self.do_clean_and_build()
