from Platform import Platform

class AndroidPlatform(Platform):
    def __init__(self, api_level):
        Platform.__init__(self)
        self.api_level = api_level
    
    def identifier(self):
        return 'android'

    def toolchain(self, architecture):
        if architecture.find('arm') >= 0:
            return 'arm-linux-androideabi-4.9'
        else:
            raise ValueError('unsupported architecture')

    def toolchain_path(self, architecture):
        path = os.path.join(self.ndk_home(), 'toolchains', self.toolchain(architecture), 'prebuilt', 'darwin-x86_64')
        if not os.path.exists(path):
            raise ValueError('missing toolchain: %s' % path)
        return path

    def sysroot_path(self, architecture):
        arch_directory = None

        if architecture == 'arm64':
            arch_directory = 'arch-arm64'
        elif architecture.find('arm') >= 0:
            arch_directory = 'arch-arm'
        else:
            raise ValueError('unsupported architecture')

        return os.path.join(self.ndk_home(), 'platforms', 'android-%d' % self.api_level, arch_directory)

    def ndk_home(self):
        ndk_home = os.getenv('ANDROID_NDK_HOME', os.getenv('NDK_HOME'))
        if not ndk_home:
            raise RuntimeError('unable to locate ndk')
        return ndk_home
