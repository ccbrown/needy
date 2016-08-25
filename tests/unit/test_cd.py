import os

from pyfakefs import fake_filesystem_unittest

from needy.cd import cd, current_directory


class CDTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_cd(self):
        root = current_directory()
        self.fs.CreateDirectory(os.path.join('tmp', 'a', 'b'))
        with cd(os.path.join('tmp', 'a')) as a:
            self.assertEqual(current_directory(), os.path.join(root, 'tmp', 'a'))
            with cd('b') as b:
                self.assertEqual(current_directory(), os.path.join(root, 'tmp', 'a', 'b'))
