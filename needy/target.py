class Target:
    def __init__(self, platform, architecture=None):
        self.platform = platform
        self.architecture = architecture

        if architecture is None:
            self.archicture = platform.default_architecture()
