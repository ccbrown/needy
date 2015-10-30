from .appletvos import AppleTVPlatform

import platform


class AppleTVSimulatorPlatform(AppleTVPlatform):
    def __init__(self, parameters):
        AppleTVPlatform.__init__(self, parameters)

    @staticmethod
    def identifier():
        return 'appletvsimulator'

    def default_architecture(self):
        return platform.machine()

    @staticmethod
    def add_arguments(parser):
        pass

    @staticmethod
    def detection_macro(architecture):
        return 'TARGET_OS_TV && TARGET_OS_SIMULATOR'
