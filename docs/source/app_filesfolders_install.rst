.. _app_filesfolders_install:


Filesfolders Installation
^^^^^^^^^^^^^^^^^^^^^^^^^

This document provides instructions and guidelines for installing the
``filesfolders`` app to be used with your SODAR Core enabled Django site.

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.


Django Settings
===============

The filesfolders app is available for your Django site after installing
``django-sodar-core``. Add the app, along with the prerequisite
``django_db_storage`` app into ``THIRD_PARTY_APPS`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'filesfolders.apps.FilesfoldersConfig',
        'db_file_storage',
    ]

Next set the ``db_file_storage`` app as the default storage app for your site:

.. code-block:: python

    DEFAULT_FILE_STORAGE = 'db_file_storage.storage.DatabaseFileStorage'


Fill out filesfolders app settings to fit your site. The settings variables are
explained below:

* ``FILESFOLDERS_MAX_UPLOAD_SIZE``: Max size for an uploaded file in bytes (int)
* ``FILESFOLDERS_MAX_ARCHIVE_SIZE``: Max size for an archive file to be unpacked
  in bytes (int)
* ``FILESFOLDERS_SERVE_AS_ATTACHMENT``: If true, always serve downloaded files
  as attachment instead of opening them in browser (bool)
* ``FILESFOLDERS_LINK_BAD_REQUEST_MSG``: Message to be displayed for a bad
  public link request (string)

Example of default values:

.. code-block:: python

    # Filesfolders app settings
    FILESFOLDERS_MAX_UPLOAD_SIZE = env.int(
        'FILESFOLDERS_MAX_UPLOAD_SIZE', 10485760)
    FILESFOLDERS_MAX_ARCHIVE_SIZE = env.int(
        'FILESFOLDERS_MAX_ARCHIVE_SIZE', 52428800)
    FILESFOLDERS_SERVE_AS_ATTACHMENT = False
    FILESFOLDERS_LINK_BAD_REQUEST_MSG = 'Invalid request'


URL Configuration
=================

In the Django URL configuration file, add the following lines under
``urlpatterns`` to include filesfolders URLs in your site. The latter line is
required by ``db_file_storage`` and should be obfuscated from actual users.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^files/', include('filesfolders.urls')),
        url(r'^OBFUSCATED_STRING_HERE/', include('db_file_storage.urls')),
    ]


Migrate Database and Register Plugin
====================================

To migrate the Django database and register the filesfolders app plugin, run the
following management command:

.. code-block:: console

    $ ./manage.py migrate

In addition to the database migration operation, you should see the following
output:

.. code-block:: console

    Registering Plugin for filesfolders.plugins.ProjectAppPlugin
