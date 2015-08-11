# -*- coding: utf-8 -*-
from setuptools import setup
import hepdata_converter.version

setup(
    name='hepdata-converter',
    version=hepdata_converter.version.__version__,
    install_requires=[
        'pyyaml'
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