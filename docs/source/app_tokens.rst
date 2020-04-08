.. _app_tokens:


Tokens App
^^^^^^^^^^

The ``tokens`` site app enables users to issue and manage access tokens for REST
API views used on your SODAR Core based Django site.


Basics
======

Users can use this app to create and delete access tokens. These can be
set to expire or work until deleted.


Installation
============

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.

Django Settings
---------------

The siteinfo app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'tokens.apps.TokensConfig',
    ]

URL Configuration
-----------------

In the Django URL configuration file, add the following line under
``urlpatterns`` to include siteinfo URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^tokens/', include('tokens.urls')),
    ]

Register Plugin
---------------

To register the siteinfo site app plugin, run the following management command:

.. code-block:: console

    $ ./manage.py syncplugins

You should see the following output:

.. code-block:: console

    Registering Plugin for tokens.plugins.SiteAppPlugin


Usage
=====

When logged in to SODAR, you can find the "API Tokens" link in your user
dropdown menu in the top right corner of the site.

Select "Create Token" from the "Token Operations" dropdown to create a new
token. You will only see the token once, so make sure to copy it to clipboard at
this point.

Deleting existing tokens can be done from the token list.
