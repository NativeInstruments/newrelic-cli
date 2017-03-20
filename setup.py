#!/usr/bin/env python
from setuptools import find_packages, setup

from newrelic_cli.version import __version__

desc = '''
newrelic-cli A Python CLI client and library for New Relic's API
================================================================

.. image::\
 https://travis-ci.org/NativeInstruments/newrelic-cli.svg?branch=master
    :target: https://travis-ci.org/NativeInstruments/newrelic-cli

newrelic-cli allows setting up your New Relic monitors using simple CLI tool.
Also it provides a set of libraries that can be easily integrated in other
Python projects. It is based on `v3` version of the API when possible,
falling back to `v2` when features are not available in `v3`.


Currently only Synthetics monitors and alerts are supported.

Documentation
=============
For more information see `GitHub page \
<https://github.com/NativeInstruments/newrelic-cli>`_.
'''

setup(
    name='newrelic-cli',
    version=__version__,
    description='Newrelic CLI client',
    long_description=desc,
    author='Native Instruments GmbH',
    author_email='cloud-devops+github@native-instruments.de',
    license='MIT',
    url='https://github.com/NativeInstruments/newrelic-cli',
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
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7'
    ],
)
