#!/usr/bin/env python

import os
import zipfile

from setuptools import setup
from setuptools.command.bdist_egg import bdist_egg as _bdist_egg


class bdist_egg(_bdist_egg):
    def run(self):
        _bdist_egg.run(self)
        with open(self.egg_output, 'rb') as f:
            data = f.read()
        with open(self.egg_output, 'wb') as f:
            f.write('#!/usr/bin/env python\n'.encode() + data)
        z = zipfile.ZipFile(self.egg_output, 'a')
        z.writestr('__main__.py', 'from needy.__main__ import main\nimport sys\nsys.exit(main(sys.argv))')
        z.close()


def read_file(path):
    with open(os.path.join(os.path.dirname(__file__), path)) as fp:
        return fp.read()

setup(
    name='needy',
    version='0.0',
    description='Dependency management utility.',
    url='https://github.com/ccbrown/needy',
    long_description=read_file('README.md'),
    author='Christopher Brown',
    author_email='ccbrown112@gmail.com',
    packages=[
        'needy',
        'needy.generators',
        'needy.platforms',
        'needy.projects',
        'needy.sources'
    ],
    entry_points={
        'console_scripts': [
            'needy = needy.__main__:main'
        ]
    },
    install_requires=[
        'colorama', 'jinja2', 'pyyaml'
    ],
    cmdclass={'bdist_egg': bdist_egg},
    license='MIT'
)
