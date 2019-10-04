.. introspection documentation master file, created by
   sphinx-quickstart on Wed Feb  7 17:05:15 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to introspection's documentation!
=========================================

|

This module is a collection of new or improved introspection functions.

Some functions are improved versions of the functions found in the `inspect module <https://docs.python.org/3/library/inspect.html>`_, others are completely new.

|

The two fundamental concepts are modeled by the :class:`Signature` and :class:`Parameter` classes.

Most functions will return instances of these classes, so it's important to know about them.

|

The available functions have been roughly categorized by what they return or what kind of objects they operate on.

|

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   signatures_and_parameters
   callables
   classes
   callstack
   misc


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
