.. _app_userprofile:


Userprofile App
^^^^^^^^^^^^^^^

The ``userprofile`` app is a site app which provides a user profile view for
projectroles compatible Django users and management of user specific settings.


Installation
============

It is **strongly recommended** to install the userprofile app into your site
when using projectroles, unless you require a specific user profile providing
app of your own.

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.

Django Settings
---------------

The userprofile app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'userprofile.apps.UserprofileConfig',
    ]

URL Configuration
-----------------

In the Django URL configuration file, add the following line under
``urlpatterns`` to include userprofile URLs in your site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'^user/', include('userprofile.urls')),
    ]

Register Plugin
---------------

To register the app plugin, run the following management command:

.. code-block:: console

    $ ./manage.py syncplugins

You should see the following output:

.. code-block:: console

    Registering Plugin for userprofile.plugins.ProjectAppPlugin


Usage
=====

After successful installation, the link for "User Profile" should be available
in the user dropdown menu in the top-right corner of the website UI after you
have logged in.


User Settings
=============

User settings are configured in the ``app_settings`` dictionary in your project
app plugins.

User settings defined in the ``projectroles`` app, available for all SODAR Core
using sites:

Display Project UUID Copying Link
    If set true, display a link in the project title bar for copying the project
    UUID into the clipboard.
Additional Email
    In addition to the default user email, also send email notifications to
    these addresses.

In the development setup, the SODAR Core example site apps also provide
additional settings for demonstrating settings features.
