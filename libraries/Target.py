import os

class Target:
	def __init__(self, platform = 'host', architecture = None):
		self.platform = platform
		self.architecture = architecture

		if platform != 'host' and architecture == None:
			raise ValueError('an architecture must be specified')