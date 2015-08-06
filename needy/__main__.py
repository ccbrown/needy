import argparse
import os
import sys

from needy import Needy
from target import Target

def main(args=sys.argv):
    try:
        parser = argparse.ArgumentParser(description='Satisfies needs.')
        parser.add_argument('--target', default='host', help='builds needs for this target (example: ios:armv7)')
        parser.add_argument('--universal-binary', help='builds the universal binary with the given name')
        parser.add_argument('--android-api-level', default='21', help='the android API level to build for')
        parser.add_argument('--minimum-ios-version', default='5.0', help='the minimum iOS version to build for')
        parameters = parser.parse_args(args[1:])
    
        needy = Needy(os.path.abspath('needs.json'), parameters)
    
        print 'Satisfying needs for: %s' % needy.path
        print 'Needs directory: %s' % needy.needs_directory
    
        if parameters.target or parameters.universal_binary == None:
            parts = parameters.target.split(':')
            platform = needy.platform(parts[0])
            target = Target(platform, parts[1] if len(parts) > 1 else platform.default_architecture())
            needy.satisfy_target(target)
    
        if parameters.universal_binary:
            needy.satisfy_universal_binary(parameters.universal_binary)
    except Exception as e:
        print '[ERROR]', e
        raise

if __name__ == "__main__":
    sys.exit(main(sys.argv))
