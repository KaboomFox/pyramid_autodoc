pyramid_autodoc
---------------

Sphinx extension for documenting your Pyramid APIs.

Install
-------

.. code-block:: bash

    pip install pyramid_autodoc

Getting Started
---------------

To use ``pyramid_autodoc`` you just need to add it to the ``extensions``
section of your Sphinx ``conf.py`` file:

.. code-block:: python

    # conf.py
    extensions = [..., 'pyramid_autodoc']

Then just create a new ``.rst`` document that uses the ``pyramid-autodoc``
directive and provide the path to your Pyramid's .ini file. Here is an example:

.. code-block:: rst

    Welcome to my Pyramid app's API docs
    ====================================

    These are the best APIs in the world!

    .. autopyramid:: /path/to/development.ini

Then you can just run your ``sphinx-build`` command and it will autogenerate
API documentation from your Pyramid routes and view docstrings.

We also support using sphinxcontrib-httpdomain_ format, just use the
``:format:`` setting:

.. code-block:: rst

    Welcome to my Pyramid app's API docs
    ====================================

    These are the best APIs in the world!

    .. autopyramid:: /path/to/development.ini
        :format: httpdomain

Ignoring Endpoints
----------------------
If you have a set of endpoints that you don't want documented you can use
``:undoc-endpoints:`` like this:

.. code-block:: rst

    Welcome to my Pyramid app's API docs
    ====================================

    These are the best APIs in the world!

    .. autopyramid:: /path/to/development.ini
        :undoc-endpoints:
          myapp.v1.views.method_name
          myapp.v2.views.other_name

.. _sphinxcontrib-httpdomain: http://pythonhosted.org/sphinxcontrib-httpdomain/
