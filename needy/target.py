class Target:
    def __init__(self, platform, architecture=None):
        self.platform = platform
        self.architecture = architecture

        if architecture is None:
            self.architecture = platform.default_architecture()

    def __str__(self):
        return '{}:{}'.format(self.platform.identifier(), self.architecture)
