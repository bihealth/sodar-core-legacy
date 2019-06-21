.. _app_sodarcache_install:


Sodarcache Installation
^^^^^^^^^^^^^^^^^^^^^^^

This document provides instructions and guidelines for installing the
``sodarcache`` app to be used with your SODAR Core enabled Django site.

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.


Django Settings
===============

The sodarcache app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'sodarcache.apps.SodarCacheConfig',
    ]

You also need to add the sodarcache backend plugin in enabled backend
plugins.

.. code-block:: python

    ENABLED_BACKEND_PLUGINS = [
        # ...
        'sodar_cache',
    ]


URL Configuration
=================

In the Django URL configuration file, add the following lines under
``urlpatterns`` to include sodarcache URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^cache/', include('sodarcache.urls')),
    ]


Migrate Database and Register Plugin
====================================

To migrate the Django database and register the sodarcache app plugin, run the
following management command:

.. code-block:: console

    $ ./manage.py migrate

In addition to the database migration operation, you should see the following
output:

.. code-block:: console

    Registering Plugin for sodarcache.plugins.BackendPlugin
