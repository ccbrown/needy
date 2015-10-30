from .iphoneos import iPhonePlatform

import platform


class iPhoneSimulatorPlatform(iPhonePlatform):
    def __init__(self, parameters):
        iPhonePlatform.__init__(self, parameters)

    @staticmethod
    def identifier():
        return 'iphonesimulator'

    def default_architecture(self):
        return platform.machine()

    @staticmethod
    def add_arguments(parser):
        pass

    @staticmethod
    def detection_macro(architecture):
        if architecture == 'x86_64':
            return 'TARGET_OS_IOS && TARGET_OS_SIMULATOR && __LP64__'
        elif architecture == 'i386':
            return 'TARGET_OS_IOS && TARGET_OS_SIMULATOR && !__LP64__'
        return None
