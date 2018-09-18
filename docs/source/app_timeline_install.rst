.. _app_timeline_install:


Timeline Installation
^^^^^^^^^^^^^^^^^^^^^

This document provides instructions and guidelines for installing the
``timeline`` app to be used with your SODAR Core enabled Django site.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.


Django Settings
===============

The timeline app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as
follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'timeline.apps.TimelineConfig',
    ]

To add timeline app settings, insert the following (change values where
applicable):

.. code-block:: python

    # Timeline app settings
    TIMELINE_PAGINATION = 15    # Number of events to be shown on one page


URL Configuration
=================

In the Django URL configuration file, add the following line under
``urlpatterns`` to include timeline URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^timeline/', include('timeline.urls')),
    ]


Migrate Database and Register Plugin
====================================

To migrate the Django database and register the timeline app/backend plugins,
run the following management command:

.. code-block:: console

    $ ./manage.py migrate

In addition to the database migration operation, you should see the following
output:

.. code-block:: console

    Registering Plugin for timeline.plugins.ProjectAppPlugin
    Registering Plugin for timeline.plugins.BackendPlugin
