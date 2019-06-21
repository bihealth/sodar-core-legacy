.. _app_bgjobs_install:


Bgjobs Installation
^^^^^^^^^^^^^^^^^^^

This document provides instructions and guidelines for installing the
``bgjobs`` app to be used with your SODAR Core enabled Django site.

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.


Django Settings
===============

The bgjobs app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as
follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'bgjobs.apps.BgjobsConfig',
    ]


URL Configuration
=================

In the Django URL configuration file, add the following line under
``urlpatterns`` to include bgjobs URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^bgjobs/', include('bgjobs.urls')),
    ]


Migrate Database and Register Plugin
====================================

To migrate the Django database and register the bgjobs app and job type plugins,
run the following management command:

.. code-block:: console

    $ ./manage.py migrate

In addition to the database migration operation, you should see the following
output:

.. code-block:: console

    Registering Plugin for bgjobs.plugins.ProjectAppPlugin
    Registering Plugin for bgjobs.plugins.BackgroundJobsPluginPoint


Celery Setup
============

**TODO**
