..
    This file is part of HEPData.
    Copyright (C) 2016 CERN.

    HEPData is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    HEPData is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with HEPData; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.


============
Installation
============

To use this package, you first need to install `YODA <https://yoda.hepforge.org>`_ and `ROOT <https://root.cern.ch>`_ (including `PyROOT <https://root.cern.ch/pyroot>`_).
Check that you can ``import yoda`` and ``import ROOT`` from Python.  You might want to install into a dedicated virtual environment:

.. code-block:: console

   $ mkvirtualenv hepdata-converter
   (hepdata-converter)$ pip install hepdata-converter

This will install the latest released version from `PyPI <https://pypi.python.org/pypi/hepdata-converter>`_.  Developers might want to instead install the project directly from GitHub in editable mode:

.. code-block:: console

   $ workon hepdata-converter
   (hepdata-converter)$ git clone https://github.com/HEPData/hepdata-converter
   (hepdata-converter)$ cd hepdata_converter
   (hepdata-converter)$ pip install -e .

Developers can then run the tests with the following command:

.. code:: bash

    python -m unittest discover hepdata_converter/testsuite 'test_*'