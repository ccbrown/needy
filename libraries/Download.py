import os
import urllib2
import binascii
import hashlib
import shutil
import StringIO
import tarfile
import zipfile


class Download:
    def __init__(self, url, checksum, destination, cache_directory):
        self.url = url
        self.checksum = checksum
        self.destination = destination
        self.cache_directory = cache_directory
        self.local_download_path = os.path.join(cache_directory, checksum)

    def clean(self):
        if not self.checksum:
            raise ValueError('checksums are required for downloads')

        self.__fetch()

        print 'Verifying checksum...'
        self.__verify_checksum()
        print 'Checksum verified.'

        print 'Unpacking to %s' % self.destination
        self.__clean_destination_dir()
        self.__unpack()
        self.__trim_lone_dirs()

    def __fetch(self):
        if not os.path.exists(self.cache_directory):
            os.makedirs(self.cache_directory)

        if not os.path.isfile(self.local_download_path):
            print 'Downloading from %s' % self.url
            download = urllib2.urlopen(self.url, timeout=5)
            with open(self.local_download_path, 'wb') as local_file:
                while True:
                    chunk = download.read(4 * 1024)
                    if not chunk:
                        break
                    local_file.write(chunk)
            del download

    def __verify_checksum(self):
        checksum = binascii.unhexlify(self.checksum)

        if len(checksum) != hashlib.md5().digest_size:
            raise ValueError('unknown checksum type')

        with open(self.local_download_path, 'rb') as file:
            file_contents = file.read()
            hash = hashlib.md5()
            hash.update(file_contents)
            if checksum != hash.digest():
                raise ValueError('incorrect checksum')

    def __clean_destination_dir(self):
        if os.path.exists(self.destination):
            shutil.rmtree(self.destination)
        os.makedirs(self.destination)

    def __unpack(self):
        if tarfile.is_tarfile(self.local_download_path):
            self.__tarfile_unpack()
            return
        if zipfile.is_zipfile(self.local_download_path):
            self.__zipfile_unpack()
            return

    def __tarfile_unpack(self):
        file_contents = ''
        with open(self.local_download_path, 'rb') as file:
            file_contents = file.read()

        file_contents_io = StringIO.StringIO(file_contents)
        tar = tarfile.open(fileobj=file_contents_io, mode='r|*')
        tar.extractall(self.destination)
        del tar
        del file_contents_io

    def __zipfile_unpack(self):
        with zipfile.ZipFile(self.local_download_path, 'r') as file:
            file.extractall(self.destination)

    def __trim_lone_dirs(self):
        temporary_directory = os.path.join(self.cache_directory, 'temp_')

        while True:
            destination_contents = os.listdir(self.destination)
            if len(destination_contents) != 1:
                break
            lone_directory = os.path.join(self.destination, destination_contents[0])
            if not os.path.isdir(lone_directory):
                break
            shutil.move(lone_directory, temporary_directory)
            shutil.rmtree(self.destination)
            shutil.move(temporary_directory, self.destination)
