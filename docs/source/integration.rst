Integration Guide
^^^^^^^^^^^^^^^^^

.. warning::
   Under construction!

This document provides instructions and guidelines for integrating the SODAR
Projectroles app into your Django site.

**NOTE:** the display of this document in Gitlab is incomplete and all listings
will be missing. Please click "display source" if you want to read this in
Gitlab.


Django Site Guidelines
======================

New Django Site
---------------

If you are *not* integrating projectroles into an existing Django site, it is
recommended to use `cookiecutter-django <https://github.com/pydanny/cookiecutter-django>`_
to set up your Django site.

.. warning::
   Currently, SODAR Projectroles only supports Django 1.11.x, while Cookiecutter
   sets up Django 2.0.x by default. It is strongly recommended to use Django
   1.11 LTS for time being. Compatibility with 2.0 and upwards is not
   guaranteed!

Make sure to set up a virtual Python environment for development with required
packages.

Existing Django Site
--------------------

If integrating into an existing Django site, please see
``requirements/base.txt`` in the projectroles repository to ensure no
requirements clash between projectroles and your site.

.. warning::
   The rest of this documentation assumes that the project has been set up using
   `cookiecutter-django <https://github.com/pydanny/cookiecutter-django>`_. If
   your Django site has not been created using it, file structures and settings
   variables may differ.


Installation
============

First, add the projectroles package requirement to your
``requirements/base.txt`` file.

At the time of writing the package is in development, so it is recommended to
clone a specific commit before we reach a stable 0.1.0 release. Example of a
row to add to your ``base.txt`` file:

.. code-block::
   -e git+ssh://git@cubi-gitlab.bihealth.org/CUBI_Engineering/CUBI_Data_Mgmt/sodar_projectroles.git@91986edb2b82af26310606e582db3e34165ae834#egg=sodar-projectroles

Install the requirements now containing the projectroles package:

.. code-block::
   $ pip -r requirements/base.txt

Projectroles should now be installed to be used with your Django site and we can
move on to configure your Django site to run and support the projectroles app.

.. hint::
   You can always refer to ``example_site`` in the projectroles repository for
   a working example of a Cookiecutter-based Django site integrating
   projectroles. However, note that some aspects of the site configuration may
   vary depending on the used cookiecutter-django version.


Django Settings
===============

You need to modify your default Django settings file. Usually this is found
within your site under ``config/settings/base.py``. For older sites the file
name may also be ``common.py``. Naturally, you should make sure no settings in
other configuration files conflict with ones set here.

For values retrieved from environment variables, make sure to configure your env
accordingly.


Site Package and Paths
----------------------

Modify the definitions at the start of the configuration as
follows (substitute "SITE_NAME" with the name of your site package).

.. code-block::
   import environ
   SITE_PACKAGE = 'SITE_NAME'
   ROOT_DIR = environ.Path(__file__) - 3
   APPS_DIR = ROOT_DIR.path(SITE_PACKAGE)

Apps
----

Add projectroles and other required apps into ``THIRD_PARTY_APPS``. The
following lines need to be included in the list:

.. code-block::
   THIRD_PARTY_APPS = [
       # ...
       'crispy_forms',
       'rules.apps.AutodiscoverRulesConfig',
       'djangoplugins',
       'pagedown',
       'markupfield',
       'rest_framework',
       'knox',
       'sodar_projectroles.projectroles.apps.ProjectrolesConfig'
   ]

Database
--------

Under ``DATABASES``, set the following value:

.. code-block::
   DATABASES['default']['ATOMIC_REQUESTS'] = False

.. note::
   If this conflicts with your existing set up, you can modify the code in your
   other apps to use e.g. ``@transaction.atomic``

Templates
---------

Under ``TEMPLATES['OPTIONS']['context_processors']``, add the line:

.. code-block::
   'sodar_projectroles.projectroles.context_processors.urls_processor',

Email
-----

Under ``EMAIL`` or ``EMAIL_CONFIGURATION``, add the following lines:

.. code-block::
   EMAIL_SENDER = env('EMAIL_SENDER', default='noreply@example.com')
   EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', default='')

Authentication
--------------

Modify ``AUTHENTICATION_BACKENDS`` to contain the following:

.. code-block::
   AUTHENTICATION_BACKENDS = [
        'rules.permissions.ObjectPermissionBackend',
        'django.contrib.auth.backends.ModelBackend',
   ]

.. note::
   The default setup by cookiecutter-django adds the ``allauth`` package. This
   can be left out of the project as it mostly provides adapters for e.g.
   social media account logins.

It is also recommended to set the value of ``LOGIN_REDIRECT_URL`` as follows:

.. code-block::
   LOGIN_REDIRECT_URL = 'home'

Django REST Framework
---------------------

Add the following structure to the configuration file:

.. code-block::
   REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
            'knox.auth.TokenAuthentication',
        ),
    }

General Site Settings
---------------------

For display in Projectroles based templates, set the following variables to
relevant values.

.. code-block::
   SITE_TITLE = 'Name of Your Project'
   SITE_SUBTITLE = env.str('SITE_SUBTITLE', 'Beta')
   SITE_INSTANCE_TITLE = env.str('SITE_INSTANCE_TITLE', 'Deployment Instance Name')

Projectroles Settings
---------------------

Fill out Projectroles settings to fit your site. The settings variables are
explained below:

* ``PROJECTROLES_SECRET_LENGTH``: Character length of secret token used in
  Projectroles
* ``PROJECTROLES_INVITE_EXPIRY_DAYS``: Days until project email invites expire
* ``PROJECTROLES_SEND_EMAIL``: Enable/disable email sending
* ``PROJECTROLES_HELP_HIGHLIGHT_DAYS``: Days for highlighting tour help for new
  users
* ``PROJECTROLES_SEARCH_PAGINATION``: Amount of search results per each app to
  display on one page

Example:

.. code-block::
   # Projectroles app settings
   PROJECTROLES_SECRET_LENGTH = 32
   PROJECTROLES_INVITE_EXPIRY_DAYS = env.int('PROJECTROLES_INVITE_EXPIRY_DAYS', 14)
   PROJECTROLES_SEND_EMAIL = env.bool('PROJECTROLES_SEND_EMAIL', False)
   PROJECTROLES_HELP_HIGHLIGHT_DAYS = 7
   PROJECTROLES_SEARCH_PAGINATION = 5

Backend App Settings
--------------------

Add a variable to list enabled backend plugins implemented using
``BackendPluginPoint``. For developing backend apps, see the ``development``
documentation.

.. code-block::
   ENABLED_BACKEND_PLUGINS = env.list('ENABLED_BACKEND_PLUGINS', None, [])

LDAP/AD Configuration
---------------------

If you want to utilize LDAP/AD user logins as configured by projectroles, you
can add the following configuration. Please make sure to add the related env
variables to your configuration.

The following lines are **mandatory** in the configuration file:

.. code-block::
   ENABLE_LDAP = env.bool('ENABLE_LDAP', False)
   ENABLE_LDAP_SECONDARY = env.bool('ENABLE_LDAP_SECONDARY', False)

The following lines are **optional**. If only using one LDAP/AD server, you can
leave the "secondary LDAP server" values unset.

.. code-block::
   if ENABLE_LDAP:
       import itertools
       import ldap
       from django_auth_ldap.config import LDAPSearch

       # Default values
       LDAP_DEFAULT_CONN_OPTIONS = {ldap.OPT_REFERRALS: 0}
       LDAP_DEFAULT_FILTERSTR = '(sAMAccountName=%(user)s)'
       LDAP_DEFAULT_ATTR_MAP = {
           'first_name': 'givenName', 'last_name': 'sn', 'email': 'mail'}

       # Primary LDAP server
       AUTH_LDAP_SERVER_URI = env.str('AUTH_LDAP_SERVER_URI', None)
       AUTH_LDAP_BIND_DN = env.str('AUTH_LDAP_BIND_DN', None)
       AUTH_LDAP_BIND_PASSWORD = env.str('AUTH_LDAP_BIND_PASSWORD', None)
       AUTH_LDAP_CONNECTION_OPTIONS = LDAP_DEFAULT_CONN_OPTIONS

       AUTH_LDAP_USER_SEARCH = LDAPSearch(
           env.str('AUTH_LDAP_USER_SEARCH_BASE', None),
           ldap.SCOPE_SUBTREE, LDAP_DEFAULT_FILTERSTR)
       AUTH_LDAP_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
       AUTH_LDAP_USERNAME_DOMAIN = env.str('AUTH_LDAP_USERNAME_DOMAIN', None)
       AUTH_LDAP_DOMAIN_PRINTABLE = env.str('AUTH_LDAP_DOMAIN_PRINTABLE', None)

       AUTHENTICATION_BACKENDS = tuple(itertools.chain(
           ('sodar_projectroles.projectroles.user_backends.PrimaryLDAPBackend',),
           AUTHENTICATION_BACKENDS,))

       # Secondary LDAP server
       if ENABLE_LDAP_SECONDARY:
           AUTH_LDAP2_SERVER_URI = env.str('AUTH_LDAP2_SERVER_URI', None)
           AUTH_LDAP2_BIND_DN = env.str('AUTH_LDAP2_BIND_DN', None)
           AUTH_LDAP2_BIND_PASSWORD = env.str('AUTH_LDAP2_BIND_PASSWORD', None)
           AUTH_LDAP2_CONNECTION_OPTIONS = LDAP_DEFAULT_CONN_OPTIONS

           AUTH_LDAP2_USER_SEARCH = LDAPSearch(
               env.str('AUTH_LDAP2_USER_SEARCH_BASE', None),
               ldap.SCOPE_SUBTREE, LDAP_DEFAULT_FILTERSTR)
           AUTH_LDAP2_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
           AUTH_LDAP2_USERNAME_DOMAIN = env.str('AUTH_LDAP2_USERNAME_DOMAIN')
           AUTH_LDAP2_DOMAIN_PRINTABLE = env.str(
               'AUTH_LDAP2_DOMAIN_PRINTABLE', None)

           AUTHENTICATION_BACKENDS = tuple(itertools.chain(
               ('sodar_projectroles.projectroles.user_backends.SecondaryLDAPBackend',),
               AUTHENTICATION_BACKENDS,))

Logging (Optional)
------------------

**TODO**
