import os
import sys
import difflib
import textwrap

from contextlib import contextmanager


try:
    import colorama
    Fore = colorama.Fore
    Style = colorama.Style
except ImportError:
    class EmptyStringAttributes:
        def __getattr__(self, name):
            return ''
    Fore = EmptyStringAttributes()
    Style = EmptyStringAttributes()


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


def dedented_unified_diff(*args, **kwargs):
    content = []
    markers = []
    header = []
    for l in [l for l in difflib.unified_diff(*args, **kwargs)]:
        if l.startswith('---') or l.startswith('+++') or l.startswith('@@'):
            header.append(l)
        elif l.startswith('-'):
            markers.append(l[:1])
            content.append(l[1:])
        elif l.startswith('+'):
            markers.append(l[:1])
            content.append(l[1:])
        elif l.startswith(' '):
            markers.append(l[:1])
            content.append(l[1:])
        else:
            markers.append(l)
            content.append(l)
    content = textwrap.dedent('\n'.join(content)).split('\n')
    return header + [m + c for m, c in zip(markers, content)]
