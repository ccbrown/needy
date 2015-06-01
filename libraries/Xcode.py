import Project, os, subprocess

def project(target, configuration, directory, needy):
	if target.platform != 'host' and target.platform != 'iphone':
		return None

	xcodebuild_args = []

	if 'xcode-project' in configuration:
		xcodebuild_args.extend(['-project', configuration['xcode-project']])

	original_directory = os.getcwd()
	os.chdir(directory)		

	try:
		with open(os.devnull, 'w') as devnull:
			subprocess.check_call(['xcodebuild', '-list'] + xcodebuild_args, stdout=devnull)
	except:
		return None
	finally:
		os.chdir(original_directory)

	return XcodeProject(target, configuration, directory, needy)

class XcodeProject(Project.Project):
	def __init__(self, target, configuration, directory, needy):
		Project.Project.__init__(self, target, configuration, directory, needy)

	def build(self, output_directory):
		import shutil

		xcodebuild_args = ['-parallelizeTargets', 'ONLY_ACTIVE_ARCH=YES', 'USE_HEADER_SYMLINKS=YES']

		if 'xcode-project' in self.configuration:
			xcodebuild_args.extend(['-project', self.configuration['xcode-project']])

		if self.target.platform == 'iphone':
			xcodebuild_args.extend(['-sdk', 'iphoneos'])
		
		if self.target.architecture:
			xcodebuild_args.extend(['-arch', self.target.architecture])

		extras_build_dir = os.path.join(output_directory, 'extras')

		subprocess.check_call(['xcodebuild'] + xcodebuild_args + [
			'INSTALL_PATH=%s' % extras_build_dir, 
			'INSTALL_ROOT=/',
			'SKIP_INSTALL=NO',
			'PUBLIC_HEADERS_FOLDER_PATH=%s' % os.path.join(output_directory, 'include'),
			'PRIVATE_HEADERS_FOLDER_PATH=%s' % os.path.join(output_directory, 'include'),
			'install', 'installhdrs'
		])

		lib_extensions = ['.a', '.dylib', '.so', '.la']
		lib_directory = os.path.join(output_directory, 'lib')

		if not os.path.exists(lib_directory):
			os.makedirs(lib_directory)

		for file in os.listdir(extras_build_dir):
			name, extension = os.path.splitext(file)
			if extension in lib_extensions:
				shutil.move(os.path.join(extras_build_dir, file), lib_directory)
		
		if not os.listdir(extras_build_dir):
			os.rmdir(extras_build_dir)
