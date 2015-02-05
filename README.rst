pyramid_autodoc
--------------------------------
Sphinx extension for documenting your Pyramid APIs.

Getting Started
--------------------------------
To use ``pyramid_autodoc`` you just need to add it to the ``extensions`` section
of your conf.py. Then just create a new ``.rst`` document that uses the
``pyramid-autodoc``.  Here is an example:

.. code-block:: rst

    Welcome to AnSvc API docs
    ===================================

    These are the best APIs in the world

    .. pyramid-autodoc::
       :ini: development.ini

Then you can just run your ``sphinx-build`` and it'll autogenerate API
documentation from your pyramid routes and docstrings.
