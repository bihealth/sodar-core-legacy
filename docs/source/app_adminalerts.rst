.. _app_adminalerts:


Adminalerts App
^^^^^^^^^^^^^^^

The ``adminalerts`` site app enables system administrators to display site-wide
messages to all users with an expiration date.


Basics
======

The app displays un-dismissable small alerts on the top of page content to all
users. They can be used to e.g. warn users of upcoming downtime or highlight
recently deployed changes.

Upon creation, an expiration date is set for each alert. Alerts can also be
freely enabled, disabled or deleted by superuser on the app UI. Additional
information regarding an alert can be provided with Markdown syntax and viewed
on a separate details page.


Installation
============

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.

Django Settings
---------------

The adminalerts app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'adminalerts.apps.AdminalertsConfig',
    ]

Optional Settings
-----------------

To alter default adminalerts app settings, insert the following **optional**
variables with values of your choosing:

.. code-block:: python

    # Adminalerts app settings
    ADMINALERTS_PAGINATION = 15    # Number of alerts to be shown on one page (int)

URL Configuration
-----------------

In the Django URL configuration file, add the following line under
``urlpatterns`` to include adminalerts URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^alerts/', include('adminalerts.urls')),
    ]

Migrate Database and Register Plugin
------------------------------------

To migrate the Django database and register the adminalerts site app plugin,
run the following management command:

.. code-block:: console

    $ ./manage.py migrate

In addition to the database migration operation, you should see the following
output:

.. code-block:: console

    Registering Plugin for admimnalert.plugins.SiteAppPlugin


Usage
=====

When logged in as a superuser, you can find the "Alerts" option in your user
dropdown menu in the top right corner of the site. Using the UI, you can add,
modify and delete alerts shown to users.

This application is not available for users with a non-superuser status.
