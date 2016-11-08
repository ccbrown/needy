class FileCache:
    @staticmethod
    def type():
        '''type of cache'''
        raise NotImplementedError('type')

    def description(self):
        '''uri, path, or other human-readable configuration description'''
        raise NotImplementedError('description')

    @staticmethod
    def from_dict(d):
        '''inverse of to_dict. returns a file cache'''
        raise NotImplementedError('from_dict')

    def set(self, key, source):
        '''make file at source retrievable with key'''
        raise NotImplementedError('set')

    def get(self, key, destination):
        '''if True is returned, the given key is now available at the given destination path'''
        raise NotImplementedError('get')
