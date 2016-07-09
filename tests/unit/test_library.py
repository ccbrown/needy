import os
from pyfakefs import fake_filesystem_unittest

from needy.library import Library


class LibraryTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_generate_pkgconfig_with_no_lib(self):
        Library.generate_pkgconfig('/', 'test')
        self.assertTrue(os.path.exists('/lib/pkgconfig/test.pc'))
        with open('/lib/pkgconfig/test.pc', 'r') as f:
            self.assertTrue('prefix=/' in f.read())

    def test_generate_pkgconfig_with_single_lib(self):
        self.fs.CreateFile('/lib/libtest.a')
        Library.generate_pkgconfig('/', 'test')
        self.assertTrue(os.path.exists('/lib/pkgconfig/test.pc'))
        with open('/lib/pkgconfig/test.pc', 'r') as f:
            self.assertTrue('-ltest' in f.read())

    def test_generate_pkgconfig_with_multiple_libs(self):
        self.fs.CreateFile('/lib/liba.a')
        self.fs.CreateFile('/lib/libb.a')
        Library.generate_pkgconfig('/', 'test')

        self.assertTrue(os.path.exists('/lib/pkgconfig/a.pc'))
        with open('/lib/pkgconfig/a.pc', 'r') as f:
            self.assertTrue('-la' in f.read())

        self.assertTrue(os.path.exists('/lib/pkgconfig/b.pc'))
        with open('/lib/pkgconfig/b.pc', 'r') as f:
            self.assertTrue('-lb' in f.read())

        self.assertTrue(os.path.exists('/lib/pkgconfig/test.pc'))
        with open('/lib/pkgconfig/test.pc', 'r') as f:
            contents = f.read()
            self.assertTrue('prefix=/' in contents)
            self.assertTrue('-la' in contents)
            self.assertTrue('-lb' in contents)
