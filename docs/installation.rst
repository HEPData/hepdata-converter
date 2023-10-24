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

Normal HEPData users and data submitters should not need to install this package, since it is
automatically invoked when uploading a single text file with extension ``.oldhepdata`` to the
`hepdata.net <https://hepdata.net>`_ submission system, or when requesting one of the
alternative output formats via the web interface.

To install this package locally, you first need to install `YODA <https://yoda.hepforge.org>`_ and
`ROOT <https://root.cern.ch>`_ (including `PyROOT <https://root.cern/manual/python/>`_).  Check that you can
``import yoda`` and ``import ROOT`` from Python.  You might want to install into a dedicated `virtual environment
<https://docs.python.org/3/tutorial/venv.html>`_:

.. code-block:: console

    $ python3 -m venv hepdata-converter
    $ source hepdata-converter/bin/activate
    (hepdata-converter)$ pip install hepdata-converter

This will install the latest released version from `PyPI <https://pypi.python.org/pypi/hepdata-converter>`_.


Developers
----------

Developers might want to instead install the project directly from
`GitHub <https://github.com/HEPData/hepdata-converter>`_ in editable mode:

.. code-block:: console

    $ git clone https://github.com/HEPData/hepdata-converter
    $ cd hepdata-converter
    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv)$ pip install -e '.[tests]'

Developers can then run the tests with the following command:

.. code:: bash

    python -m unittest discover hepdata_converter/testsuite 'test_*'


Docker
------

Alternatively, a `Docker <https://www.docker.com>`_ image is available (see
the `hepdata-converter-docker <https://github.com/HEPData/hepdata-converter-docker>`_ repository)
containing the dependencies such as YODA and ROOT, but not the ``hepdata-converter`` package itself.

.. code-block:: console

    $ docker pull hepdata/hepdata-converter
    $ docker run --rm -it hepdata/hepdata-converter /bin/bash

The ``hepdata-converter`` package can be installed inside the Docker container:

.. code-block:: console

    root@617be04cbab5:/# pip install hepdata-converter
    root@617be04cbab5:/# hepdata-converter -h
    root@617be04cbab5:/# python -c 'import hepdata_converter'

Note that the Docker container will be automatically removed when it exits (if running with the ``--rm`` option).  The
Python module or CLI can then be used as described in :doc:`Usage <usage>`.  Input and output files can be moved
between the local filesystem and the running Docker container using the ``docker cp`` command, for example,

.. code-block:: console

    $ docker cp sample.oldhepdata 617be04cbab5:/
    root@617be04cbab5:/# hepdata-converter -i oldhepdata sample.oldhepdata SampleYAML
    $ docker cp 617be04cbab5:/SampleYAML .

where the prompt ``$`` indicates a terminal corresponding to the local filesystem and the prompt
``root@617be04cbab5:/#`` indicates another terminal corresponding to the running Docker container.

Alternatively, developers can install from `GitHub <https://github.com/HEPData/hepdata-converter>`_ and
mount the current directory of the local filesystem when running the Docker container:

.. code-block:: console

    $ git clone https://github.com/HEPData/hepdata-converter
    $ cd hepdata-converter
    $ docker run -v $PWD:$PWD -w $PWD --rm -it hepdata/hepdata-converter /bin/bash
    root@2c22e88402d2:/hepdata-converter# pip install -e '.[tests]'
    root@2c22e88402d2:/hepdata-converter# hepdata-converter -h
    root@2c22e88402d2:/hepdata-converter# python -c 'import hepdata_converter'
    root@2c22e88402d2:/hepdata-converter# python -m unittest discover hepdata_converter/testsuite 'test_*'