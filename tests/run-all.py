#!/usr/bin/env python

import argparse
import os
import shutil
import subprocess
import sys

tests_directory = os.path.dirname(os.path.realpath(__file__))
needy_path = os.path.join(tests_directory, '..', 'needy.py')

def test(directory, needy_args, run_dirty=False):
    print 'Running test in %s: %s' % (directory, ' '.join(needy_args))
    os.chdir(directory)
    if not run_dirty and os.path.exists('needs'):
        shutil.rmtree('needs')
    subprocess.check_call([needy_path] + needy_args)

def main(args):
    parser = argparse.ArgumentParser(description='Tests Needy.')
    parser.add_argument('--run-dirty', default=False, action='store_true', help='run without cleaning first (useful for saving time while debugging)')
    parameters = parser.parse_args(args[1:])
    
    for entry in os.listdir(tests_directory):
        test_directory = os.path.join(tests_directory, entry)
        if os.path.isfile(os.path.join(test_directory, 'needs.json')):
            test(test_directory, [], parameters.run_dirty)
            test(test_directory, ['--target=ios:armv7'], parameters.run_dirty)
            test(test_directory, ['--target=android:armv7'], parameters.run_dirty)

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print '[ERROR]', e
        raise
