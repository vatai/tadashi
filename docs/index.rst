.. Tadashi documentation master file, created by
   sphinx-quickstart on Fri Sep 20 11:02:34 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tadashi documentation
=====================


Work In Progress!!!

Tadashi can be installed from `PyPI`_.

.. _PyPI: https://pypi.org/project/tadashi/


.. mermaid::

  flowchart TB
    subgraph apps["Files on disc"]
      direction TB
      app["orig.c"]
      tapp["new.c"]
    end
    subgraph states["States of the polyhedral representation"]
      direction TB
      S1["State0"]
      S2["State1"]
      S3["State2"]
      S1-- "`legal = node.transform()`" -->S2
      S2-- "`legal = node.transform()`" -->S3
    end
    app-. "`node = app.scops[0].schedule_tree[42]`" .-> S1
    S3-. "`tapp = app.generate_code()`".-> tapp
    S3-. "`app.reset_scops()`".-> S1

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
   :maxdepth: 1
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`

.. * :ref:`search` # this search page doesn't work for some reason... might look into it once

.. toctree::
   :maxdepth: 1
