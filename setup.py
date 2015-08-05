#!/usr/bin/env python

from setuptools import setup

setup(
    name='needy', 
    version='0.0',
    description='Dependency management utility',
    packages=['needy', 'needy.platforms', 'needy.projects'],
    entry_points={
        'console_scripts': [
            'needy = needy.__main__:main'
        ]
    }
)