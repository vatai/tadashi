.. Tadashi documentation master file, created by
   sphinx-quickstart on Fri Sep 20 11:02:34 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tadashi documentation
=====================


.. mermaid::

  flowchart LR
    subgraph apps["Files on disc"]
      direction TB
      app["orig.c"]
      tapp["new.c"]
    end
    subgraph states["States of the polyhedral representation"]
      direction TB
      S1["$$S1$$"]
      S2["$$S_2$$"]
      S3["$$S_3$$"]
      S1-- "`legal = node.transform()`" -->S2
      S2-- "`legal = node.transform()`" -->S3
    end
    app-. "`node = app.scops[0].schedule_tree[42]`" .-> S1
    S3-. "`tapp = app.generate_code()`".-> tapp

Add your :math:`x` content using ``reStructuredText`` syntax. See the
`reStructuredText <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
documentation for details.


.. To get started take a look at the `quick start guide`_ or the `examples`_.

.. # .. _quick start guide: https://github.com/Spin-Chemistry-Labs/radicalpy/tree/main/docs/quick-start/guide.org
.. # .. _examples: https://github.com/Spin-Chemistry-Labs/radicalpy/tree/main/examples
.. # .. _documentation: https://radicalpy.readthedocs.io/

.. Installation
.. ------------

.. Install simply using :code:`pip`::
..   pip install tadashi


.. toctree::
   :maxdepth: 2
   :caption: Contents:


.. include:: modules.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`

.. * :ref:`search` # this search page doesn't work for some reason... might look into it once

.. toctree::
   :maxdepth: 1
