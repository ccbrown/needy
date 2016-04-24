#!/usr/bin/env python

import os

from setuptools import setup


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
    license='MIT'
)
