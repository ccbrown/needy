import os
from pyfakefs import fake_filesystem_unittest

from needy.sources.download import Download


class DownloadTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_get(self):
        Download.get('https://github.com/USCiLab/cereal/archive/v1.1.2.tar.gz',
                     'fd65224cf628119fe1d85cbca63214c4f6a82e75',
                     'destination'
                     )
        self.assertTrue(os.path.exists('destination'))

    def test_get_with_incorrect_checksum(self):
        with self.assertRaises(ValueError):
            Download.get('https://github.com/USCiLab/cereal/archive/v1.2.0.tar.gz',
                         'fd65224cf628119fe1d85cbca63214c4f6a82e75',
                         'destination'
                         )
        self.assertFalse(os.path.exists('destination'))
