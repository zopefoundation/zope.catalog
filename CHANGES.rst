Changes
=======

4.1.0 (unreleased)
------------------

- Add support for PyPy (PyPy3 support is blocked on a PyPy3-compatible
  release of ``zodbpickle``).

- Convert doctests to Sphinx documentation, including building docs
  and running doctest snippets under ``tox``.

4.0.0 (2014-12-24)
------------------

- Add support for Python 3.4.

4.0.0a1 (2013-02-25)
--------------------

- Add support for Python 3.3.

- Replace deprecated ``zope.interface.implements`` usage with equivalent
  ``zope.interface.implementer`` decorator.

- Drop support for Python 2.4 and 2.5.

3.8.2 (2011-11-29)
------------------

- Conform to repository policy.

3.8.1 (2009-12-27)
------------------

- Remov ``zope.app.testing`` dependency.

3.8.0 (2009-02-01)
------------------

- Move core functionality from ``zope.app.catalog`` to this package.
  The ``zope.app.catalog`` package now only contains ZMI-related browser
  views and backward-compatibility imports.
