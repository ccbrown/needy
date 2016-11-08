import time

from pyfakefs import fake_filesystem_unittest

from needy.caches.directory import DirectoryCache


class DirectoryTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_directory_cache(self):
        cache = DirectoryCache('cache')
        self.assertEquals(cache.type(), 'directory')
        self.assertEquals(cache.description(), 'cache')

        self.assertFalse(cache.get('key', 'tmp'))

        self.fs.CreateFile('a', contents='AAA')
        self.assertTrue(cache.set('a', 'a'))
        self.assertTrue(cache.get('a', 'tmp'))
        with open('tmp', 'r') as f:
            self.assertEquals(f.read(), 'AAA')

        cache.prune()
        self.assertTrue(cache.get('a', 'tmp'))

        distant_past = time.time() - 60 * 60 * 24 * 30
        self.fs.GetObject(cache._object_path('a')).st_atime = distant_past

        cache.prune()
        self.assertFalse(cache.get('a', 'tmp'))
