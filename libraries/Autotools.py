import glob, Project, os

def project(target, configuration, directory, needy):
	if os.path.isfile(os.path.join(directory, 'configure')) and glob.glob(os.path.join(directory, '*akefile.in')):
		return AutotoolsProject(target, configuration, directory, needy)
	if os.path.isfile(os.path.join(directory, 'autogen.sh')) and os.path.isfile(os.path.join(directory, 'configure.ac')) and os.path.isfile(os.path.join(directory, 'Makefile.am')):
		return AutotoolsProject(target, configuration, directory, needy)
	return None

class AutotoolsProject(Project.Project):
	def __init__(self, target, configuration, directory, needy):
		Project.Project.__init__(self, target, configuration, directory, needy)

	def configure(self, output_directory):
		import subprocess
		
		if not os.path.isfile(os.path.join(self.directory, 'configure')):
			subprocess.check_call('./autogen.sh')
		
		configure_args = self.configuration['configure-args'] if 'configure-args' in self.configuration else []

		configure_args.append('--prefix=%s' % output_directory)
	
		if self.target.platform == 'host':
			pass
		elif self.target.platform == 'iphone':
			configure_host = self.__available_configure_host([
				'%s-apple-darwin' % self.target.architecture, 'arm*-apple-darwin', 'arm-apple-darwin', 'arm*', 'arm'
			])

			if configure_host == 'arm*-apple-darwin':
				configure_host = '%s-apple-darwin' % self.target.architecture
			elif configure_host == 'arm*':
				configure_host = self.target.architecture

			configure_args.extend([
				'CFLAGS=-mios-version-min=5.0',
				'CC=xcrun -sdk iphoneos clang -arch %s' % self.target.architecture,
				'CXX=xcrun -sdk iphoneos clang++ -arch %s' % self.target.architecture,
				'--host=%s' % configure_host
			])
		elif self.target.platform == 'android':
			toolchain = self.needy.android_toolchain_path(self.target.architecture)
			sysroot = self.needy.android_sysroot_path(self.target.architecture)
			
			if self.target.architecture.find('arm') >= 0:
				configure_host = self.__available_configure_host([
					'linux*android*', 'arm*', 'arm'
				])
				
				if configure_host == 'linux*android*':
					configure_host = 'arm-linux-androideabi'
				elif configure_host == 'arm*':
					configure_host = self.target.architecture

				configure_args.extend([
					'CFLAGS=-mthumb -march=%s' % self.target.architecture
				])

				binary_prefix = 'arm-linux-androideabi'
			else:
				raise ValueError('unsupported architecture')

			fixed_path = '%s:%s:%s' % (os.path.join(toolchain, binary_prefix, 'bin'), os.path.join(toolchain, 'bin'), os.environ['PATH'])

			configure_args.extend([
				'PATH=%s' % fixed_path,
				'CC=%s-gcc --sysroot=%s' % (binary_prefix, sysroot),
				'CXX=%s-g++ --sysroot=%s' % (binary_prefix, sysroot),
				'--host=%s' % configure_host,
				'--with-sysroot=%s' % sysroot
			])			
		else:
			raise ValueError('unsupported platform')

		if 'linkage' in self.configuration:
			if self.configuration['linkage'] == 'static':
				configure_args.append('--disable-shared')
				configure_args.append('--enable-static')
			elif self.configuration['linkage'] == 'dynamic':
				configure_args.append('--disable-static')
				configure_args.append('--enable-shared')
			else:
				raise ValueError('unknown linkage')

		subprocess.check_call(['./configure'] + configure_args)

	def build(self, output_directory):
		import subprocess
		
		make_args = []

		if self.target.platform == 'android':
			toolchain = self.needy.android_toolchain_path(self.target.architecture)
			if self.target.architecture.find('arm') >= 0:
				binary_prefix = 'arm-linux-androideabi'
			else:
				raise ValueError('unsupported architecture')
			fixed_path = '%s:%s:%s' % (os.path.join(toolchain, binary_prefix, 'bin'), os.path.join(toolchain, 'bin'), os.environ['PATH'])
			make_args.append('PATH=%s' % fixed_path)

		subprocess.check_call(['make', '-j8'] + make_args)
		subprocess.check_call(['make', 'install'] + make_args)

	def __available_configure_host(self, candidates):
		with open(os.path.join(self.directory, 'configure'), 'r') as file:
			contents = file.read()
			for candidate in candidates:
				if contents.find(candidate) >= 0:
					return candidate

		return None
