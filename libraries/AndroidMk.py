import Project, os

def project(target, configuration, directory, needy):
	if target.platform == 'android' and os.path.exists(os.path.join(directory, 'Android.mk')):
		return AndroidMkProject(target, configuration, directory, needy)
	return None

class AndroidMkProject(Project.Project):
	def __init__(self, target, configuration, directory, needy):
		Project.Project.__init__(self, target, configuration, directory, needy)

	def build(self, output_directory):
		import shutil, subprocess
		
		if self.target.architecture == 'armv7':
			abi = 'armeabi-v7a'
		elif self.target.architecture == 'arm':
			abi = 'armeabi'
		else:
			raise ValueError('unsupported architecture')

		ndk_build_args = [
			'NDK_PROJECT_PATH=.',
			'APP_BUILD_SCRIPT=./Android.mk',
			'NDK_LIBS_OUT=%s' % os.path.join(output_directory, 'lib-temp'),
			'NDK_TOOLCHAIN=%s' % self.needy.android_toolchain(self.target.architecture),
			'APP_PLATFORM=%s' % self.needy.android_platform(),
			'APP_ABI=%s' % abi
		]
		
		subprocess.check_call(['ndk-build'] + ndk_build_args)
		shutil.move(os.path.join(output_directory, 'lib-temp', abi), os.path.join(output_directory, 'lib'))
		shutil.rmtree(os.path.join(output_directory, 'lib-temp'))
