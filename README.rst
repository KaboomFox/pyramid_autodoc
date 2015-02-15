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
If you have a set of endpoints that you don't want to group or skip entirely
there are a few options you can use:

- ``:match-path:`` - Whitelist only a specific set of paths
- ``:skip-path:`` - Blacklist a specific set of paths
- ``:match-module:`` - Whitelist a set of modules
- ``:skip-module:`` - Blacklist a set of modules

.. code-block:: rst

    Welcome to my Pyramid app's API docs
    ====================================

    These are the best APIs in the world!

    .. autopyramid:: /path/to/development.ini
        :skip-module:
          ^myapp.v1.*
        :match-path:
          ^/data

Linking to Source Code
----------------------

If you want to link from the endpoint to the source code for the corresponding
views and you are using sphinx.ext.viewcode_, you can generate links to the
source code pages it generates.  Alternatively, if your source is on the web,
you can generate external links instead.

- ``:link-code:`` - Enable links from endpoints to source code.  Assumes
  sphinx.ext.viewcode_ is being used unless ``link-code-pattern`` is specified.
- ``:link-code-pattern:`` - Pattern URL for generating links to source code.
  Tokens in the pattern are replaced by the following values.

  - ``{file}`` is replaced by the file path, e.g. ``pyramid_autodoc/utils.py``.
  - ``{lineno_start}`` is replaced by the beginning line number of the view, e.g.
    ``17``.
  - ``{lineno_end}`` is replaced by the end line number of the view, e.g.
    ``22``.

.. code-block:: rst

    Welcome to my Pyramid app's API docs
    ====================================

    Links to source code within the docs.

    .. autopyramid:: /path/to/development.ini
        :link-code:

    Links to source code on GitHub.

    .. autopyramid:: /path/to/development.ini
        :link-code:
        :link-code-pattern: https://github.com/SurveyMonkey/pyramid_autodoc/blob/master/{file}#L{lineno_start}-L{lineno_end}

In the last example, a generated link would look like
``https://github.com/SurveyMonkey/pyramid_autodoc/blob/master/pyramid_autodoc/utils.py#L17-L22``.

.. _sphinxcontrib-httpdomain: http://pythonhosted.org/sphinxcontrib-httpdomain/
.. _sphinx.ext.viewcode: http://sphinx-doc.org/ext/viewcode.html
