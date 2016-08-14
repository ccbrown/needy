import logging
import os
import subprocess
import sys

try:
    from colorama import Style
except ImportError:
    class EmptyStringAttributes:
        def __getattr__(self, name):
            return ''
    Style = EmptyStringAttributes()

from .cd import current_directory
from .filesystem import TempDir


def __log_check_output(cmd, verbosity, **kwargs):
    shell = not isinstance(cmd, list)
    with open(os.devnull, 'w') as devnull:
        logging.log(verbosity, __format_command(cmd))
        return subprocess.check_output(cmd, stderr=devnull, shell=shell, **kwargs).decode()


def __log_check_call(cmd, verbosity, **kwargs):
    shell = not isinstance(cmd, list)
    with open(os.devnull, 'w') as devnull:
        logging.log(verbosity, __format_command(cmd))
        if verbosity < logging.getLogger().getEffectiveLevel():
            subprocess.check_call(cmd, stderr=devnull, shell=shell, stdout=devnull, **kwargs)
        else:
            subprocess.check_call(cmd, stderr=subprocess.STDOUT, shell=shell, **kwargs)


def command(cmd, verbosity=logging.INFO, environment_overrides={}):
    __log_check_call(cmd, verbosity, env=__environment(environment_overrides))


def command_output(cmd, verbosity=logging.INFO, environment_overrides={}):
    logging.log(verbosity, __format_command(cmd))
    return __log_check_output(cmd, verbosity, env=__environment(environment_overrides))


def command_sequence(cmds, verbosity=logging.INFO, environment_overrides={}):
    with open(os.devnull, 'w') as devnull:
        stderr = devnull if verbosity < logging.getLogger().getEffectiveLevel() else subprocess.STDOUT
        stdout = devnull if verbosity < logging.getLogger().getEffectiveLevel() else None
        if sys.platform == 'win32':
            with TempDir() as d:
                path = os.path.join(d, 'script.cmd')
                with open(path, 'wb') as f:
                    f.write('\r\n'.join(cmds).encode())
                subprocess.check_call(['cmd', '/c', 'call', path], stderr=stderr, stdout=stdout, env=__environment(environment_overrides))
        else:
            subprocess.check_call(['sh', '-c', '\n'.join(['set -ex'] + cmds)], stderr=stderr, stdout=stdout, env=__environment(environment_overrides))


def __environment(environment_overrides):
    environment_overrides['PWD'] = current_directory()
    env = os.environ.copy()
    env.update(environment_overrides)
    return {key: str(value) for key, value in env.items()}


def __format_command(cmd):
    return Style.BRIGHT + '{}'.format(cmd) + Style.RESET_ALL
