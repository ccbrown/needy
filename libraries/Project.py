def evaluate_conditionals(configuration, target):
	if not 'conditionals' in configuration:
		return configuration
	
	ret = configuration.copy()

	for conditional in configuration['conditionals']:
		is_true = True
		for key, value in conditional.iteritems():
			if not is_true:
				break
		
			if key == 'true' or key == 'false':
				continue
			
			if key == 'platform':
				is_true = (target.platform in value) if isinstance(value, list) else (target.platform == value)
			else:
				raise ValueError('unknown conditional key')
		
		if is_true:
			if 'true' in conditional:
				ret.update(conditional['true'])
		elif 'false' in conditional:
			ret.update(conditional['false'])

	return ret

class Project:
	def __init__(self, target, configuration, directory, needy):
		self.target = target
		self.configuration = evaluate_conditionals(configuration, target) if configuration else dict()
		self.directory = directory
		self.needy = needy

	def pre_build(self, output_directory):
		import shlex, subprocess
	
		if 'pre-build' in self.configuration:
			for command in self.configuration['pre-build']:
				subprocess.check_call(shlex.split(command))
	
	def post_build(self, output_directory):
		import shlex, subprocess
	
		if 'post-build' in self.configuration:
			for command in self.configuration['post-build']:
				subprocess.check_call(shlex.split(command.format(build_directory=output_directory)))
