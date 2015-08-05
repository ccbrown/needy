class Target:
    def __init__(self, platform, architecture):
        self.platform = platform
        self.architecture = architecture

        if architecture is None:
            raise ValueError('an architecture must be specified')
