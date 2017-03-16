#!/usr/bin/env python
from setuptools import find_packages, setup

from newrelic_cli.version import __version__

setup(
    name='newrelic-cli',
    version=__version__,
    description='Newrelic CLI client',
    author='Native Instruments GmbH',
    packages=find_packages(),
    # production requirements
    install_requires=[
        'requests>=2.0.0',
        'jinja2',
        'pyyaml'
    ],
    tests_require=[
        'requests_mock',
        'nose',
        'tox'
    ],
    test_suite='nose.collector',
    entry_points={
        'console_scripts': ['newrelic-cli=newrelic_cli.cli:main']
    },
    classifiers=[
        'License :: OSI Approved :: MIT License'
    ],
)
