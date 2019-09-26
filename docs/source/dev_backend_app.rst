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


- ``javascript_url``: Path to on demand includeable Javascript file
- ``css_url``: Path to on demand includeable CSS file
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

Including Backend Javascript/CSS
--------------------------------

If you want Javascript or CSS files to be associated with your plugin you can
set the ``javascript_url`` or ``css_url`` variables to specify the path to your
file. Note that these should correspond to ``STATIC`` paths under your app
directory.

.. code-block:: python

    class BackendPlugin(BackendPluginPoint):

        name = 'example_backend_app'
        title = 'Example Backend App'
        javascript_url = 'example_backend_app/js/example.js'
        css_url = 'example_backend_app/css/example.css'

The ``get_backend_include`` template-tag will return a ``<script>`` or
``<link>`` html tag with your specific file path, to be used in a template of
your app making use of the backend plugin:

.. code-block:: django

    {% load projectroles_common_tags %}
    {% get_backend_include 'example_backend_app' 'js' as javascript_include_tag %}
    {{ javascript_include_tag|safe }}

    {% get_backend_include 'example_backend_app' 'css' as css_include_tag %}
    {{ css_include_tag|safe }}

This will result in the following HTML:

.. code-block:: html

    <script type="text/javascript" src="/static/example.js"></script>
    <link rel="stylesheet" type="text/css" href="/static/example.css"/>

Be sure to use the backend plugin's name (not the title) as the key and filter
the result by ``safe``, so the tag won't be auto-escaped.
