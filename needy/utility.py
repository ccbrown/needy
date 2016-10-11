import os
import sys

from contextlib import contextmanager


class DummyContextManager():
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_value, traceback):
        return False


@contextmanager
def log_section(name):
    # While undocumented, the 'travis_fold' marker has apparently been
    # around for a while. This is what provides Travis-CI with the collapsible
    # activity sections.
    if os.environ.get('CI', '') == 'true' and os.environ.get('TRAVIS', '') == 'true':
        activity_name = '-'.join(name.split())
        sys.stdout.write('travis_fold:start:{}\r'.format(activity_name))
        yield
        sys.stdout.write('travis_fold:end:{}\r'.format(activity_name))
    else:
        yield
