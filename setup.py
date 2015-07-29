# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='hepdata-converter',
    version='0.1',
    requires=['pyyaml'],
    packages=['hepdata_converter', 'hepdata_converter.parsers', 'hepdata_converter.writers', 'hepdata_converter.testsuite'],
    url='',
    license='',
    author='Michał Szostak',
    author_email='michal.florian.szostak@cern.ch',
    description='Library providing means of conversion between oldhepdata format to new one, and new one to csv / yoda / root etc.'
)