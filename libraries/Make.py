import Project, os

def project(target, configuration, directory, needy):
	if os.path.isfile(os.path.join(directory, 'Makefile')):
		return MakeProject(target, configuration, directory, needy)
	return None

class MakeProject(Project.Project):
	def __init__(self, target, configuration, directory, needy):
		Project.Project.__init__(self, target, configuration, directory, needy)

	def configure(self, output_directory):
		import fileinput, re, sys

		excluded_targets = []
		
		if self.target.platform != 'host':
			excluded_targets.extend(['test', 'tests', 'check'])

		with open('Makefile', 'r') as makefile:
			with open('MakefileNeedyGenerated', 'w') as needy_makefile:
				for line in makefile.readlines():
					uname_assignment = re.match('(.+=).*shell .*uname', line, re.MULTILINE)
					if uname_assignment and self.target.platform == 'android':
						needy_makefile.write('%sLinux\n' % uname_assignment.group(1))
						continue
				
					excluded_target = None
					for target in excluded_targets:
						if line.find('%s:' % target) == 0:
							excluded_target = target
							break

					if excluded_target:
					    needy_makefile.write('%s:\nneedy-excluded-%s-for-non-host-platform:\n' % (excluded_target, excluded_target))
					    continue

					needy_makefile.write(line)
    
	def build(self, output_directory):
		import re, subprocess
		
		make_args = ['-f', './MakefileNeedyGenerated', '-j8']
		path_override = None

		target_os = None

		if self.target.platform == 'host':
			pass
		elif self.target.platform == 'iphone':
			make_args.extend([
				'CFLAGS=-mios-version-min=5.0',
				'CC=xcrun -sdk iphoneos clang -arch %s' % self.target.architecture,
				'CXX=xcrun -sdk iphoneos clang++ -arch %s' % self.target.architecture,
			])
		elif self.target.platform == 'android':
			toolchain = self.needy.android_toolchain_path(self.target.architecture)
			sysroot = self.needy.android_sysroot_path(self.target.architecture)
			
			if self.target.architecture.find('arm') >= 0:
				make_args.extend([
					'CFLAGS=-mthumb -march=%s' % self.target.architecture,
				])
				binary_prefix = 'arm-linux-androideabi'
			else:
				raise ValueError('unsupported architecture')			

			path_override = '%s:%s:%s' % (os.path.join(toolchain, binary_prefix, 'bin'), os.path.join(toolchain, 'bin'), os.environ['PATH'])

			make_args.extend([
				'CC=%s-gcc --sysroot=%s' % (binary_prefix, sysroot),
				'CXX=%s-g++ --sysroot=%s' % (binary_prefix, sysroot),
				'AR=%s-ar' % binary_prefix,
				'RANLIB=%s-ranlib' % binary_prefix,
			])
			
			target_os = 'Linux'
		else:
			raise ValueError('unsupported platform')

		environment_overrides = dict()

		if target_os:
			make_args.extend([
				'OS=%s' % target_os,
				'TARGET_OS=%s' % target_os
			])

		if path_override:
			make_args.append('PATH=%s' % path_override)
			environment_overrides['PATH'] = path_override

		self.needy.command(['make'] + make_args, environment_overrides = environment_overrides)
		
		make_install_args = [
			'PREFIX=%s' % output_directory,
			'INSTALLPREFIX=%s' % output_directory,
			'INSTALL_PREFIX=%s' % output_directory
		]

		recon = subprocess.check_output(['make', 'install', '--recon'] + make_args + make_install_args)
		doing_things_inside_prefix = False
		doing_things_outside_prefix = False

		while True:
			match = re.search(' (/.+?[^\\\\])( |$)', recon, re.MULTILINE)
			if match == None:
				break

			path = match.group(1)
			if os.path.relpath(path, self.directory).find('..') == 0:
				if os.path.relpath(path, output_directory).find('..') == 0:
					doing_things_outside_prefix = True
				else:
					doing_things_inside_prefix = True

			recon = recon[match.end() - 1:]

		if doing_things_outside_prefix or not doing_things_inside_prefix:
			raise RuntimeError('unable to figure out how to set installation prefix')

		self.needy.command(['make', 'install'] + make_args + make_install_args, environment_overrides = environment_overrides)
