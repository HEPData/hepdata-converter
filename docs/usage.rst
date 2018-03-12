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


Usage
=====

The library exposes a single function ``convert`` which enables conversion from different input formats
(``oldhepdata``, ``yaml``) to different output formats (``csv``, ``root``, ``yaml``, ``yoda``), by using a simple in-memory
intermediary format.


Python
------

.. code:: python

    import hepdata_converter

    hepdata_converter.convert('sample.oldhepdata', 'Sample', options={'input_format': 'oldhepdata', 'output_format': 'yaml'})


CLI
---

.. code:: bash

    hepdata-converter -i oldhepdata -o yaml sample.oldhepdata Sample

The default input and output formats are ``yaml`` if not specified explicitly.

See a help message with more detailed options using ``hepdata-converter -h``.