# -*- coding: utf-8 -*-
from setuptools import setup
import re


def get_version():
    with open('hepdata_converter/version.py', 'r') as version_f:
        content = version_f.read()

    r = re.search('^__version__ *= *\'(?P<version>.+)\'', content, flags=re.MULTILINE)
    if not r:
        return '0.0.0'
    return r.group('version')

setup(
    name='hepdata-converter',
    version=get_version(),
    install_requires=[
        'pyyaml',
        'hepdata_validator'
    ],
    entry_points={
        'console_scripts': [
            'hepdata-converter = hepdata_converter:main',
        ]
    },
    packages=['hepdata_converter', 'hepdata_converter.parsers', 'hepdata_converter.writers', 'hepdata_converter.testsuite'],
    url='https://github.com/HEPData/hepdata-converter/',
    license='GPL',
    author='Michał Szostak',
    author_email='michal.florian.szostak@cern.ch',
    description='Library providing means of conversion between oldhepdata format to new one, and new one to csv / yoda / root etc.',
    download_url='https://github.com/HEPData/hepdata-converter/tarball/0.1',
)