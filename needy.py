#!/usr/bin/env python

import os, subprocess

class Needy:
	def __init__(self, path, parameters):
		import json

		self.path = path
		self.parameters = parameters

		with open(self.path, 'r') as needs_file:
			self.needs = json.load(needs_file)

		self.needs_directory = self.determine_needs_directory()

	def command(self, arguments, environment_overrides = None):
		env = None
		if environment_overrides:
			env = os.environ.copy()
			env.update(environment_overrides)
		subprocess.check_call(arguments, env = env)

	def satisfy_target(self, target):
		if not 'libraries' in self.needs:
			return

		from libraries import Library

		print 'Building libraries for %s' % target.platform
		if target.architecture:
			print 'Architecture: %s' % target.architecture

		for name, library_configuration in self.needs['libraries'].iteritems():
			directory = os.path.join(self.needs_directory, name)
			library = Library.Library(library_configuration, directory, self)
			if library.has_up_to_date_build(target):
				print '[UP-TO-DATE] %s' % name
			else:
				print '[LIBRARY] %s' % name
				library.build(target)
				print '[SUCCESS]'

	def satisfy_universal_binary(self, universal_binary):
		from libraries import Library, Target

		print 'Building universal binary for %s' % universal_binary

		if not 'universal-binaries' in self.needs:
			raise ValueError('no universal binaries defined')
		
		if not universal_binary in self.needs['universal-binaries']:
			raise ValueError('unknown universal binary')
		
		if not 'libraries' in self.needs:
			return

		configuration = self.needs['universal-binaries'][universal_binary]

		for name, library_configuration in self.needs['libraries'].iteritems():
			directory = os.path.join(self.needs_directory, name)
			library = Library.Library(library_configuration, directory, self)
			if library.has_up_to_date_universal_binary(universal_binary, configuration):
				print '[UP-TO-DATE] %s' % name
			else:
				print '[LIBRARY] %s' % name
				library.build_universal_binary(universal_binary, configuration)
				print '[SUCCESS]'
		
	def create_universal_binary(self, inputs, output):	
		name, extension = os.path.splitext(output)
		if not extension in ['.a', '.so', '.dylib']:
			return False
		
		subprocess.check_call(['lipo', '-create'] + inputs + ['-output', output])
		return True

	def determine_needs_directory(self):
		directory = os.path.dirname(self.path)
		needy_directory = directory
		
		while directory != '/':
			directory = os.path.dirname(directory)
			if os.path.isfile(os.path.join(directory, 'needs.json')):
				needy_directory = directory
		
		return os.path.join(needy_directory, 'needs')
	
	def android_platform(self):
		return self.parameters.android_platform
	
	def android_toolchain(self, architecture):
		if architecture.find('arm') >= 0:
			return 'arm-linux-androideabi-4.9'
		else:
			raise ValueError('unsupported architecture')

	def android_toolchain_path(self, architecture):
		path = os.path.join(self.android_ndk_home(), 'toolchains', self.android_toolchain(architecture), 'prebuilt', 'darwin-x86_64')
		if not os.path.exists(path):
			raise ValueError('missing toolchain: %s' % path)
		return path

	def android_sysroot_path(self, architecture):
		arch_directory = None
		
		if architecture == 'arm64':
			arch_directory = 'arch-arm64'
		elif architecture.find('arm') >= 0:
			arch_directory = 'arch-arm'
		else:
			raise ValueError('unsupported architecture')

		return os.path.join(self.android_ndk_home(), 'platforms', self.android_platform(), arch_directory)

	def android_ndk_home(self):
		ndk_home = os.getenv('ANDROID_NDK_HOME', os.getenv('NDK_HOME'))
		if not ndk_home:
			raise RuntimeError('unable to locate ndk')
		return ndk_home

def main(args):
	import argparse
	
	parser = argparse.ArgumentParser(description='Satisfies needs.')
	parser.add_argument('--target', help='builds needs for this target (example: iphone:armv7)')
	parser.add_argument('--universal-binary', help='builds the universal binary with the given name')
	parser.add_argument('--android-platform', default='android-21', help='the android platform to build for (example: android-14)')
	parameters = parser.parse_args(args[1:])

	needy = Needy(os.path.abspath('needs.json'), parameters)

	print 'Satisfying needs for: %s' % needy.path
	print 'Needs directory: %s' % needy.needs_directory

	if parameters.target or parameters.universal_binary == None:
		from libraries import Target
		if parameters.target:
			parts = parameters.target.split(':')
			target = Target.Target(parts[0], parts[1] if len(parts) > 1 else None)
		else:
			target = Target.Target('host')
		needy.satisfy_target(target)

	if parameters.universal_binary:
		needy.satisfy_universal_binary(parameters.universal_binary)

if __name__ == "__main__":
	import sys

	try:
		sys.exit(main(sys.argv))
	except Exception as e:
		print '[ERROR]', e
		raise
