import os
import logging
import distutils.spawn
import subprocess

from ..source import Source
from ..cd import cd
from ..process import command, command_output


class GitRepository(Source):
    def __init__(self, repository, commit, directory):
        Source.__init__(self)
        self.repository = repository
        self.commit = commit
        self.directory = directory

    @classmethod
    def identifier(cls):
        return 'git'

    def status_text(self):
        with cd(self.directory):
            rev_list = subprocess.check_output(['git', 'rev-list', '--left-right', '{}...'.format(self.commit)]).decode().splitlines()
            ahead = len([1 for rev in rev_list if rev[0] == '>'])
            behind = len([1 for rev in rev_list if rev[0] == '<'])
            diff = subprocess.check_output(['git', 'diff-index', 'HEAD']).decode().splitlines()

        ret = []
        if ahead:
            ret.append('{} ahead'.format(ahead))
        if behind:
            ret.append('{} behind'.format(behind))
        if diff:
            ret.append('{} file{} changed'.format(len(diff), 's' if len(diff) != 1 else ''))

        return ', '.join(ret) if ret else 'up-to-date'

    def clean(self):
        GitRepository.__assert_git_availability()

        self.__fetch_if_necessary()

        with cd(self.directory):
            command(['git', 'clean', '-xffd'], logging.DEBUG)
            command(['git', 'reset', 'HEAD', '--hard'], logging.DEBUG)
            command(['git', 'checkout', '--force', self.commit], logging.DEBUG)
            command(['git', 'submodule', 'update', '--init', '--recursive'], logging.DEBUG)

    def synchronize(self):
        GitRepository.__assert_git_availability()

        if not os.path.exists(os.path.join(self.directory, '.git')):
            self.__fetch(verbosity=logging.INFO)

        with cd(self.directory):
            command(['git', 'fetch'])
            command(['git', 'checkout', self.commit])
            command(['git', 'submodule', 'update', '--init', '--recursive'])

    def __fetch_if_necessary(self):
        if not os.path.exists(os.path.join(self.directory, '.git')):
            self.__clone()

        current_origin = self.__current_remote('origin')
        if current_origin != self.repository:
            logging.debug('changing remote \'origin\' from {} to {}'.format(current_origin, self.repository))
            self.__replace_remote('origin', self.repository)
            self.__fetch()

    def __current_remote(self, remote):
        if os.path.exists(self.directory):
            with cd(self.directory):
                try:
                    return command_output(['git', 'config', '--get', 'remote.{}.url'.format(remote)], logging.DEBUG).strip()
                except subprocess.CalledProcessError:
                    pass

    def __replace_remote(self, remote, git_url, verbosity=logging.DEBUG):
        with cd(self.directory):
            try:
                command(['git', 'remote', 'remove', 'origin'], verbosity)
            except subprocess.CalledProcessError:
                pass
            command(['git', 'remote', 'add', 'origin', self.repository], verbosity)

    def __fetch(self, verbosity=logging.DEBUG):
        with cd(self.directory):
            try:
                command(['git', 'fetch'], verbosity)
            except subprocess.CalledProcessError:
                # we should be okay with this to enable offline builds
                logging.warn('git fetch failed for {}'.format(self.directory))
                pass

    def __clone(self, verbosity=logging.DEBUG):
        if not os.path.exists(os.path.dirname(self.directory)):
            os.makedirs(os.path.dirname(self.directory))

        with cd(os.path.dirname(self.directory)):
            command(['git', 'clone', self.repository, os.path.basename(self.directory)], verbosity)

        with cd(self.directory):
            command(['git', 'submodule', 'update', '--init', '--recursive'], verbosity)

    @classmethod
    def __assert_git_availability(cls):
        if not distutils.spawn.find_executable('git'):
            raise RuntimeError('No git binary is present')
