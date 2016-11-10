#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

if not sys.version_info[0] == 3:
    print('only python3 supported!')
    sys.exit(1)

setup(
    name='testImpSHARK',
    version='0.10',
    description='Calculates dependencies of tests for python projects.',
    install_requires=['modulegraph', 'mongoengine', 'pymongo'],
    author='Fabian Trautsch',
    author_email='ftrautsch@googlemail.com',
    url='https://github.com/smartshark/testImpSHARK',
    test_suite='tests',
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache2.0 License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
