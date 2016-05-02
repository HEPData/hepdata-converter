# -*- coding: utf-8 -*-
import os
from setuptools import setup
import re


def get_all_datafiles(package, path):
    r = []
    setup_path = os.path.dirname(__file__)
    for abs_path, dirs, files in os.walk(os.path.join(setup_path, package, path)):
        r += [os.path.join(path, f) for f in files]
    return r


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
        'hepdata_validator',
        'matplotlib'
    ],
    entry_points={
        'console_scripts': [
            'hepdata-converter = hepdata_converter:main',
        ]
    },

    packages=['hepdata_converter', 'hepdata_converter.parsers', 'hepdata_converter.writers', 'hepdata_converter.testsuite'],
    package_data={'hepdata_converter': get_all_datafiles(package='hepdata_converter/testsuite', path='testdata')},
    include_package_data=True,

    url='https://github.com/HEPData/hepdata-converter/',
    license='GPL',
    author='HEPData Team',
    author_email='info@hepdata.net',
    description='Library providing means of conversion between oldhepdata format to new one, and new one to csv / yoda / root etc.',
    download_url='https://github.com/HEPData/hepdata-converter/tarball/%s' % get_version(),
)
