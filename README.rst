=================
HEPData Converter
=================


.. image:: https://img.shields.io/travis/HEPData/hepdata-converter.svg
    :target: https://travis-ci.org/HEPData/hepdata-converter

.. image:: https://coveralls.io/repos/github/HEPData/hepdata-converter/badge.svg?branch=master
    :target: https://coveralls.io/github/HEPData/hepdata-converter?branch=master

.. image:: https://img.shields.io/github/license/HEPData/hepdata-converter.svg
    :target: https://github.com/HEPData/hepdata-converter/blob/master/LICENSE

.. image:: https://img.shields.io/github/release/hepdata/hepdata-converter.svg?maxAge=2592000
    :target: https://github.com/HEPData/hepdata-converter/releases

.. image:: https://img.shields.io/github/issues/hepdata/hepdata-converter.svg?maxAge=2592000
    :target: https://github.com/HEPData/hepdata-converter/issues

.. image:: https://readthedocs.org/projects/hepdata-converter/badge/?version=latest
    :target: http://hepdata-converter.readthedocs.io/



This software library provides support for converting:

* Old HepData format (`Sample <http://hepdata.cedar.ac.uk/resource/sample.input>`_) to YAML
* YAML to:
    * `ROOT <https://root.cern.ch/>`_
    * `YODA <https://yoda.hepforge.org/>`_
    * `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_


------------
Installation
------------

To use this package, you need to have YODA and ROOT (and PyROOT) installed.
Instructions to install are available below.
Install from PyPI with ``pip install hepdata-converter``.

ROOT Installation
-----------------

We've provided some helpful installation guides for you :)

* `Download binaries (all platforms) <https://root.cern.ch/downloading-root>`_
* `Build from sources <https://root.cern.ch/installing-root-source>`_
* `Mac OS (Homebrew) Installation <http://spamspameggsandspam.blogspot.ch/2011/08/setting-up-root-and-pyroot-on-new-mac.html>`_:  ``brew install root6``

YODA Installation
-----------------

Mac OS. We use brew, you should too :) ``brew tap davidchall/hep`` to tell brew where to get package definitions from for HEP.	Then, ``brew install yoda``.


-------------
Running Tests
-------------

Simply run

.. code:: bash

    python -m unittest discover hepdata_converter/testsuite 'test_*'


-------------
Documentation
-------------

Learn more about using and extending the tool at http://hepdata-converter.readthedocs.io