.. Tadashi documentation master file, created by
   sphinx-quickstart on Fri Sep 20 11:02:34 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tadashi documentation
=====================


.. mermaid::

   sequenceDiagram
      participant Alice
      participant Bob
      Alice->John: Hello John, how are you?
      loop Healthcheck
          John->John: Fight against hypochondria
      end
      Note right of John: Rational thoughts <br/>prevail...
      John-->Alice: Great!
      John->Bob: How about you?
      Bob-->John: Jolly good!

Add your content using ``reStructuredText`` syntax. See the
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
