.. _dev_backend_app:


Backend App Development
^^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for developing
**backend apps** to be used with the SODAR Core framework.

It is recommended to read :ref:`dev_project_app` before this document.


Backend App Basics
==================

Backend apps are intended as apps used by other apps via their plugin, without
requiring hard-coded imports. These may provide their own views for e.g. Ajax
API functionality, but mostly they're intended to be internal (hence the name).


Prerequisites
=============

See :ref:`dev_project_app`.


Models
======

No specific model implementation is required. However, it is strongly to refer
to objects using ``sodar_uuid`` fields instead of the database private key.


BackendAppPlugin
================

The plugin is detected and retrieved using a ``BackendAppPlugin``.

Declaring the Plugin
--------------------

Create a file ``plugins.py`` in your app's directory. In the file, declare a
``BackendAppPlugin`` class implementing
``projectroles.plugins.BackendPluginPoint``. Within the class, implement
member variables and functions as instructed in comments and docstrings.

.. code-block:: python

    from projectroles.plugins import BackendPluginPoint
    from .urls import urlpatterns

    class BackendAppPlugin(BackendPluginPoint):
        """Plugin for registering a backend app"""
        name = 'example_backend_app'
        title = 'Example Backend App'
        urls = urlpatterns
        # ...

The following variables and functions are **mandatory**:

- ``name``: App name (ideally should correspond to the app package name)
- ``title``: Printable app title
- ``icon``: Font Awesome 4.7 icon name (without the ``fa-*`` prefix)
- ``description``: Verbose description of app
- ``get_api()``: Function for retrieving the API class for the backend, to be
  implemented

Implementing the following is **optional**:

- ``get_statistics()``: Return statistics for the siteinfo app. See details in
  :ref:`the siteinfo documentation <app_siteinfo>`.

.. hint::

    If you want to implement a backend API which is closely tied to a project
    app, there's no requirement to declare your backend as a separate Django
    app. You can just include the ``BackendAppPlugin`` in your app's
    ``plugins.py`` along with your ``ProjectAppPlugin``. See the
    :ref:`timeline app <app_timeline>` for an example of this.

Using the Plugin
----------------

To retrieve the API for the plugin, use the
function ``projectroles.plugins.get_backend_api()`` as follows:

.. code-block:: python

    from projectroles.plugins import get_backend_api
    example_api = get_backend_api('example_backend_app')

    if example_api:     # Make sure the API is there, and only after that..
        pass            # ..do stuff with the API
