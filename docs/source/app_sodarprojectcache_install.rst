.. _app_sodarprojectcache_install:


Sodar Project Cache Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document provides instructions and guidelines for installing the
``sodarprojectcache`` app to be used with your SODAR Core enabled Django site.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.


Django Settings
===============

The sodarprojectcache app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'sodarprojectcache.apps.SodarProjectCacheConfig',
    ]

You also need to add the sodarprojectcache backend plugin in enabled backend
plugins.

.. code-block:: python

    ENABLED_BACKEND_PLUGINS = [
        # ...
        'sodarprojectcache',
    ]

URL Configuration
=================

In the Django URL configuration file, add the following lines under
``urlpatterns`` to include sodarprojectcache URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^cache/', include('sodarprojectcache.urls')),
    ]


Migrate Database and Register Plugin
====================================

To migrate the Django database and register the sodarprojectcache app plugin, run the
following management command:

.. code-block:: console

    $ ./manage.py migrate

In addition to the database migration operation, you should see the following
output:

.. code-block:: console

    Registering Plugin for sodarprojectcache.plugins.BackendPlugin
