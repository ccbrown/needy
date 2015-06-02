import os

class Library:
	def __init__(self, configuration, directory, global_configuration):
		self.configuration = configuration
		self.directory = directory
		self.source_directory = os.path.join(directory, 'source')
		self.global_configuration = global_configuration

	def build(self, target):
		import shutil
	
		self.fetch()

		print 'Building for %s' % target.platform
		
		if target.architecture:
			print 'Architecture: %s' % target.architecture
		
		project = self.project(target)
		
		if not project:
			raise RuntimeError('unknown project type')
		
		build_directory = self.build_directory(target)

		if not os.path.exists(build_directory):
			os.makedirs(build_directory)

		original_directory = os.getcwd()
		os.chdir(project.directory)

		try:
			project.pre_build(build_directory)
			project.build(build_directory)
			project.post_build(build_directory)
		except:
			shutil.rmtree(build_directory)
			raise
		finally:
			os.chdir(original_directory)
	
	def build_universal_binary(self, name, configuration):
		import shutil, subprocess, Target
	
		print 'Building universal binary %s' % name

		for platform, architectures in configuration.iteritems():
			for architecture in architectures:
				target = Target.Target(platform, architecture)
				if not self.has_up_to_date_build(target):
					self.build(target)

		files = dict()
		target_count = 0

		for platform, architectures in configuration.iteritems():
			for architecture in architectures:
				target_count = target_count + 1
				target = Target.Target(platform, architecture)
				lib_directory = os.path.join(self.build_directory(target), 'lib')
				for file in os.listdir(lib_directory):
					if not os.path.isfile(os.path.join(lib_directory, file)):
						continue
					if not file in files:
						files[file] = []
					files[file].append(os.path.join(lib_directory, file))
		
		universal_binary_directory = self.universal_binary_directory(name)

		if os.path.exists(universal_binary_directory):
			shutil.rmtree(universal_binary_directory)

		universal_lib_directory = os.path.join(self.universal_binary_directory(name), 'lib')		
		os.makedirs(universal_lib_directory)

		try:
			for file, builds in files.iteritems():
				if len(builds) != target_count:
					continue
	
				file_name, extension = os.path.splitext(file)

				if extension in ['.a', '.dylib', '.so']:
					print 'Creating universal library %s' % file
					subprocess.check_call(['lipo', '-create'] + builds + ['-output', os.path.join(universal_lib_directory, file)])
		except:
			shutil.rmtree(universal_binary_directory)
			raise
		
	def has_up_to_date_build(self, target):
		# TODO: return out-of-date if our configuration changes
		return os.path.exists(self.build_directory(target))

	def has_up_to_date_universal_binary(self, name, configuration):
		# TODO: return out-of-date if our configuration changes
		return os.path.exists(self.universal_binary_directory(name))

	def build_directory(self, target):
		return os.path.join(self.directory, 'build', target.platform, target.architecture if target.architecture else 'default')

	def universal_binary_directory(self, name):
		return os.path.join(self.directory, 'build', 'universal', name)

	def fetch(self):
		if 'download' in self.configuration:
			self.__fetch_download()
		elif 'repository' in self.configuration:
			self.__fetch_git_repository()
		else:
			raise ValueError('no source specified in configuration')
	
	def __fetch_download(self):
		import binascii, hashlib, re, shutil, StringIO, tarfile, urllib2
	
		if not 'checksum' in self.configuration:
			raise ValueError('checksums are required for downloads')
	
		download_directory = os.path.join(self.directory, 'download')
		if not os.path.exists(download_directory):
			os.makedirs(download_directory)
	
		local_download_path = os.path.join(download_directory, self.configuration['checksum'])
	
		if not os.path.isfile(local_download_path):
			print 'Downloading from %s' % self.configuration['download']
			download = urllib2.urlopen(self.configuration['download'])
			with open(local_download_path, 'wb') as local_file:
				local_file.write(download.read())
			del download
	
		with open(local_download_path, 'rb') as file:
			file_contents = file.read()
		
		print 'Verifying checksum...'
		
		checksum = binascii.unhexlify(self.configuration['checksum'])
	
		if len(checksum) == hashlib.md5().digest_size:
			hash = hashlib.md5()
			hash.update(file_contents)
			if checksum != hash.digest():
				raise ValueError('incorrect checksum')
		else:
			raise ValueError('unknown checksum type')
	
		print 'Checksum verified.'
		
		print 'Unpacking to %s' % self.source_directory
	
		if os.path.exists(self.source_directory):
			shutil.rmtree(self.source_directory)

		os.makedirs(self.source_directory)
	
		file_contents_io = StringIO.StringIO(file_contents)
		tar = tarfile.open(fileobj = file_contents_io, mode='r|*')
		tar.extractall(self.source_directory)
		del tar
		del file_contents_io
		
		temporary_source_directory = os.path.join(os.path.dirname(self.source_directory), 'source_')

		while True:
			source_directory_contents = os.listdir(self.source_directory)
			if len(source_directory_contents) != 1:
				break
			lone_directory = os.path.join(self.source_directory, source_directory_contents[0])
			if not os.path.isdir(lone_directory):
				break
			shutil.move(lone_directory, temporary_source_directory)
			shutil.rmtree(self.source_directory)
			shutil.move(temporary_source_directory, self.source_directory)

	def __fetch_git_repository(self):
		import subprocess

		if not os.path.exists(self.source_directory):
			os.makedirs(self.source_directory)

		original_directory = os.getcwd()
		os.chdir(self.source_directory)

		try:
			if not os.path.exists(os.path.join(self.source_directory, '.git')):
				subprocess.check_call(['git', 'clone', self.configuration['repository'], '.'])
			subprocess.check_call(['git', 'checkout', self.configuration['commit']])
			subprocess.check_call(['git', 'clean', '-xfd'])
		finally:
			os.chdir(original_directory)

	def project(self, target):
		import AndroidMk, Autotools, Make, Project, Source, Xcode

		configuration = Project.evaluate_conditionals(self.configuration['project'] if 'project' in self.configuration else dict(), target)

		candidates = [AndroidMk, Autotools, Make, Xcode]

		if 'configure-args' in configuration:
			candidates.insert(0, Autotools)

		if 'xcode-project' in configuration:
			candidates.insert(0, Xcode)

		if 'source-directory' in configuration:
			candidates.insert(0, Source)

		for candidate in candidates:
			project = candidate.project(target, configuration, self.source_directory, self.global_configuration)
			if project:
				return project
		
		raise RuntimeError('unknown project type')