import os

class Download:
	def __init__(self, url, checksum, destination, cache_directory):
		self.url = url
		self.checksum = checksum
		self.destination = destination
		self.cache_directory = cache_directory

	def fetch(self):
		import sys, urllib2
	
		if not os.path.exists(self.cache_directory):
			os.makedirs(self.cache_directory)
	
		local_download_path = os.path.join(self.cache_directory, self.checksum)
	
		if not os.path.isfile(local_download_path):
			print 'Downloading from %s' % self.url
			download = urllib2.urlopen(self.url, timeout = 5)
			with open(local_download_path, 'wb') as local_file:
				while True:
					chunk = download.read(4 * 1024)
					if not chunk:
						break
					local_file.write(chunk)
			del download	

	def clean(self):
		import binascii, hashlib, re, shutil, StringIO, tarfile, urllib2
	
		if not self.checksum:
			raise ValueError('checksums are required for downloads')
	
		local_download_path = os.path.join(self.cache_directory, self.checksum)
		if not os.path.isfile(local_download_path):
			self.fetch()

		with open(local_download_path, 'rb') as file:
			file_contents = file.read()
		
		print 'Verifying checksum...'
		
		checksum = binascii.unhexlify(self.checksum)
	
		if len(checksum) == hashlib.md5().digest_size:
			hash = hashlib.md5()
			hash.update(file_contents)
			if checksum != hash.digest():
				raise ValueError('incorrect checksum')
		else:
			raise ValueError('unknown checksum type')
	
		print 'Checksum verified.'
		
		print 'Unpacking to %s' % self.destination
	
		if os.path.exists(self.destination):
			shutil.rmtree(self.destination)

		os.makedirs(self.destination)
	
		file_contents_io = StringIO.StringIO(file_contents)
		tar = tarfile.open(fileobj = file_contents_io, mode='r|*')
		tar.extractall(self.destination)
		del tar
		del file_contents_io
		
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

