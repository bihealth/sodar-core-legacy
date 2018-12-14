.. _app_projectroles_integration:

Projectroles Integration
^^^^^^^^^^^^^^^^^^^^^^^^

This document provides instructions and guidelines for integrating projectroles
and other SODAR Core apps into your Django site.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


Installation on a New Site
**************************

If you want to set up a new site for integrating projectroles, see the
recommended options in this section.


SODAR Django Site Template
==========================

If you are *not* integrating projectroles into an existing Django site, it is
strongly recommended to use `sodar_django_site <https://cubi-gitlab.bihealth.org/CUBI_Engineering/CUBI_Data_Mgmt/sodar_django_site>`_
as a template. This project contains a minimal Django site pre-configured with
projecroles and other SODAR Core apps. The master branch version of this project
always integrates the latest stable release of SODAR Core and projectroles.

To set up your site with this template, clone the repository and follow the
installation instructions in the README.rst file.

Once you have your site set up, you can look into :ref:`customization tips <app_projectroles_custom>`
and start :ref:`developing your SODAR Core compatible apps <development>`.


Cookiecutter-Django
===================

If the SODAR Django site template does not suit your needs, it is also possible
to set up your site using `cookiecutter-django <https://github.com/pydanny/cookiecutter-django/releases/tag/1.11.10>`_.
In this case, follow the instructions in the following section as if you were
integrating SODAR Core to an existing Django site.

.. warning::

    Currently, SODAR Core only supports Django 1.11.x, while the latest versions
    of cookiecutter-django set up Django 2.0.x by default. It is strongly
    recommended to use Django 1.11 LTS for time being. Compatibility with 2.0 and
    upwards is not guaranteed! Integration into the last official
    `1.11 release <https://github.com/pydanny/cookiecutter-django/releases/tag/1.11.10>`_
    of cookiecutter-django has been tested and verified to be working.

.. note::

    The latest cookiecutter-django 1.11 release has dependencies which are
    already out of date. Please update them to match the requirements of the
    django-sodar-core package.

.. note::

    For any other issues regarding the cookiecutter-django setup, see the
    cookiecutter-django documentation.


Installation on an Existing Site
********************************


Instructions for setting up projectroles and SODAR Core on an existing Django
site or a fresh site generated with cookiecutter-django are detailed in this
chapter.

.. warning::

    In order to successfully set up projectroles, you are expected to **follow
    all the instructions here in the order they are presented**. Please note
    that leaving out steps may result in a non-working Django site!

.. warning::

    The rest of this documentation assumes that your Django project has been set
    up using a `1.11 release of cookiecutter-django <https://github.com/pydanny/cookiecutter-django/releases/tag/1.11.10>`_.
    Otherwise details such as directory structures and settings variables may
    differ.

First, add the ``django-sodar-core`` and ``djangoplugins`` package requirements
into your ``requirements/base.txt`` file.

.. note::

    At the time of writing the SODAR Core package is in development, so you'll
    need to install it from our GitLab, either by a release tag or a specific
    commit. It is recommended to use either the most recent tagged release in
    the ``master`` branch for production and the latest commit from the ``dev``
    branch for development.

Add the following rows into your ``base.txt`` file:

.. code-block:: console

    -e git://github.com/mikkonie/django-plugins.git@1bc07181e6ab68b0f9ed3a00382eb1f6519e1009#egg=django-plugins
    -e git+ssh://git@cubi-gitlab.bihealth.org/CUBI_Engineering/CUBI_Data_Mgmt/sodar_core.git@v0.2.1#egg=django-sodar-core

Install the requirements now containing the required packages:

.. code-block:: console

    $ pip install -r requirements/base.txt

SODAR Core apps and django-plugins should now be installed to be used with your
Django site.

.. hint::

    You can always refer to ``example_site`` in the projectroles repository for
    a working example of a Cookiecutter-based Django site integrating SODAR Core.
    However, note that some aspects of the site configuration may vary depending
    on the cookiecutter-django version used on your site.


Django Settings
===============

Next you need to modify your default Django settings file, usually located in
``config/settings/base.py``. For sites created with an older cookiecutter-django
version the file name may also be ``common.py``. Naturally, you should make sure
no settings in other configuration files conflict with ones set here.

For values retrieved from environment variables, make sure to configure your
env accordingly. For development and testing, using ``READ_DOT_ENV_FILE`` is
recommended.

Site Package and Paths
----------------------

Modify the definitions at the beginning of ``base.py`` as follows. Substitute
{SITE_NAME} with the name of your site package.

.. code-block:: python

    import environ
    SITE_PACKAGE = '{SITE_NAME}'
    ROOT_DIR = environ.Path(__file__) - 3
    APPS_DIR = ROOT_DIR.path(SITE_PACKAGE)

Apps
----

Add projectroles and other required apps into ``THIRD_PARTY_APPS``. The
following apps need to be included in the list:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'crispy_forms',
        'rules.apps.AutodiscoverRulesConfig',
        'djangoplugins',
        'pagedown',
        'markupfield',
        'rest_framework',
        'knox',
        'projectroles.apps.ProjectrolesConfig',
    ]

Database
--------

Under ``DATABASES``, it is recommended to set the following value:

.. code-block:: python

    DATABASES['default']['ATOMIC_REQUESTS'] = False

.. note::

    If this conflicts with your existing set up, you can modify the code in your
    other apps to use e.g. ``@transaction.atomic``.

.. note::

    This setting mostly is used for the ``sodar_taskflow`` transactions
    supported by projectroles but not commonly used, so having this setting as
    True *may* cause no issues. However, it is not officially supported at this
    time.

Templates
---------

Under ``TEMPLATES['OPTIONS']['context_processors']``, add the line:

.. code-block:: python

    'projectroles.context_processors.urls_processor',

Email
-----

Under ``EMAIL_CONFIGURATION`` or ``EMAIL``, add the following lines:

.. code-block:: python

    EMAIL_SENDER = env('EMAIL_SENDER', default='noreply@example.com')
    EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', default='')

Authentication
--------------

Modify ``AUTHENTICATION_BACKENDS`` to contain the following:

.. code-block:: python

    AUTHENTICATION_BACKENDS = [
        'rules.permissions.ObjectPermissionBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]

.. note::

    The default setup by cookiecutter-django adds the ``allauth`` package. This
    can be left out of the project if not needed, as it mostly provides adapters
    for e.g. social media account logins. If removing allauth, you can also
    remove unused settings variables starting with ``ACCOUNT_*``.

Make sure the following settings remain in your configuration:

.. code-block:: python

    AUTH_USER_MODEL = 'users.User'
    LOGIN_REDIRECT_URL = 'home'
    LOGIN_URL = 'login'


Django REST Framework
---------------------

To enable ``djangorestframework`` API views and ``knox`` authentication, add the
following to the configuration file:

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
            'knox.auth.TokenAuthentication',
        ),
    }

General Site Settings
---------------------

For display in projectroles based templates, set the following variables to
relevant values.

.. code-block:: python

    SITE_TITLE = 'Name of Your Project'
    SITE_SUBTITLE = env.str('SITE_SUBTITLE', 'Beta')
    SITE_INSTANCE_TITLE = env.str('SITE_INSTANCE_TITLE', 'Deployment Instance Name')

Projectroles Settings
---------------------

Fill out projectroles app settings to fit your site. The settings variables are
explained below:

* ``PROJECTROLES_SITE_MODE``: Site mode for remote project metadata
  synchronization, either ``SOURCE`` (allow others to read local projects) or
  ``TARGET`` (read projects from another site)
* ``PROJECTROLES_TARGET_CREATE``: Whether or not local projects can be created
  if site is in ``TARGET`` mode. If your site is in ``SOURCE`` mode, this
  setting has no effect.
* ``PROJECTROLES_INVITE_EXPIRY_DAYS``: Days until project email invites expire
  (int)
* ``PROJECTROLES_SEND_EMAIL``: Enable/disable email sending (bool)
* ``PROJECTROLES_ENABLE_SEARCH``: Whether you want to enable SODAR search on
  your site (boolean)

Example:

.. code-block:: python

    # Projectroles app settings
    PROJECTROLES_SITE_MODE = env.str('PROJECTROLES_SITE_MODE', 'TARGET')
    PROJECTROLES_TARGET_CREATE = env.bool('PROJECTROLES_TARGET_CREATE', True)
    PROJECTROLES_INVITE_EXPIRY_DAYS = env.int('PROJECTROLES_INVITE_EXPIRY_DAYS', 14)
    PROJECTROLES_SEND_EMAIL = env.bool('PROJECTROLES_SEND_EMAIL', False)
    PROJECTROLES_ENABLE_SEARCH = True

Optional Projectroles Settings
------------------------------

The following settings are **optional**:

* ``PROJECTROLES_SECRET_LENGTH``: Character length of secret token used in
  projectroles (int)
* ``PROJECTROLES_SEARCH_PAGINATION``: Amount of search results per each app to
  display on one page (int)
* ``PROJECTROLES_HELP_HIGHLIGHT_DAYS``: Days for highlighting tour help for new
  users (int)
* ``PROJECTROLES_DISABLE_CATEGORIES``: If set True, disable categories and only
  allow a list of projects on the root level (boolean) (see note)
* ``PROJECTROLES_HIDE_APP_LINKS``: Apps hidden from the project sidebar and
  dropdown menus for non-superusers. The app views and URLs are still
  accessible. The names should correspond to the ``name`` property in each
  project app's plugin (list)

Example of optional settings:

.. code-block:: python

    # Projectroles app settings
    # ...
    PROJECTROLES_SECRET_LENGTH = 32
    PROJECTROLES_SEARCH_PAGINATION = 5
    PROJECTROLES_HELP_HIGHLIGHT_DAYS = 7
    PROJECTROLES_DISABLE_CATEGORIES = True
    PROJECTROLES_HIDE_APP_LINKS = ['filesfolders']

.. warning::

    Regarding ``PROJECTROLES_DISABLE_CATEGORIES``: In the current SODAR core
    version remote site access and remote project synchronization are disabled
    if this option is used! Use only if a simple project list is specifically
    required in your site.

Backend App Settings
--------------------

Add a variable to list enabled backend plugins implemented using
``BackendPluginPoint``. For more information see :ref:`dev_backend_app`.

.. code-block:: python

    ENABLED_BACKEND_PLUGINS = env.list('ENABLED_BACKEND_PLUGINS', None, [])

SODAR API Settings
------------------

Also make sure to configure the SODAR API. The ``SODAR_API_DEFAULT_HOST``
setting should post to the externally visible host of your server and be
configured in your environment settings.

.. code-block:: python

    SODAR_API_DEFAULT_VERSION = '0.1'
    SODAR_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar+json'
    SODAR_API_DEFAULT_HOST = SODAR_API_DEFAULT_HOST = env.url('SODAR_API_DEFAULT_HOST', 'http://0.0.0.0:8000')

Logging
-------

It is also recommended to add "projectroles" under ``LOGGING['loggers']``. For
production, INFO debug level is recommended.

LDAP/AD Configuration (optional)
--------------------------------

If you want to utilize LDAP/AD user logins as configured by projectroles, you
can add the following configuration. Make sure to also add the related env
variables to your configuration.

This part of the setup is **optional**.

.. note::

    In order to support LDAP, make sure you have installed the dependencies from
    ``utility/install_ldap_dependencies.sh`` and ``requirements/ldap.txt``! For
    more information see :ref:`dev_sodar_core`.

.. note::

    If only using one LDAP/AD server, you can leave the "secondary LDAP server"
    values unset.

.. code-block:: python

    ENABLE_LDAP = env.bool('ENABLE_LDAP', False)
    ENABLE_LDAP_SECONDARY = env.bool('ENABLE_LDAP_SECONDARY', False)

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
        AUTH_LDAP_DOMAIN_PRINTABLE = env.str(
            'AUTH_LDAP_DOMAIN_PRINTABLE', AUTH_LDAP_USERNAME_DOMAIN)

        AUTHENTICATION_BACKENDS = tuple(itertools.chain(
           ('projectroles.auth_backends.PrimaryLDAPBackend',),
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
                'AUTH_LDAP2_DOMAIN_PRINTABLE', AUTH_LDAP_USERNAME_DOMAIN)

            AUTHENTICATION_BACKENDS = tuple(itertools.chain(
                ('projectroles.auth_backends.SecondaryLDAPBackend',),
                AUTHENTICATION_BACKENDS,))


User Configuration
==================

In order for SODAR Core apps to work on your Django site, you need to extend the
default user model.

Extending the User Model
------------------------

In a cookiecutter-django project, an extended user model should already exist
in ``{SITE_NAME}/users/models.py``. The abstract model provided by the
projectroles app provides the same model with critical additions, most notably
the ``sodar_uuid`` field used as an unique identifier for SODAR objects
including users.

If you have not added any of your own modifications to the model, you can simply
**replace** the existing model extension with the following code:

.. code-block:: python

    from projectroles.models import SODARUser

    class User(SODARUser):
        pass

If you need to add your own extra fields or functions (or have existing ones
already), you can add them in this model.

After updating the user model, create and run database migrations.

.. code-block:: console

    $ ./manage.py makemigrations
    $ ./manage.py migrate

.. note::

    You probably will need to edit the default unit tests under
    ``{SITE_NAME}/users/tests/`` for them to work after making these changes.
    See ``example_site.users.tests`` in this repository for an example.

Populating UUIDs for Existing Users
-----------------------------------

When integrating projectroles into an existing site with existing users, the
``sodar_uuid`` field needs to be populated. See
`instructions in Django documentation <https://docs.djangoproject.com/en/1.11/howto/writing-migrations/#migrations-that-add-unique-fields>`_
on how to create the required migrations.

Synchronizing User Groups for Existing Users
--------------------------------------------

To set up user groups for existing users, run the ``syncgroups`` management
command.

.. code-block:: console

    $ ./manage.py syncgroups

User Profile Site App
---------------------

The ``userprofile`` site app is installed with SODAR Core. It adds a user
profile page in the user dropdown. Use of the app is not mandatory but
recommended, unless you are already using some other user profile app. See
the :ref:`userprofile app documentation <app_userprofile>` for instructions.

Add Login Template
------------------

You should add a login template to ``{SITE_NAME}/templates/users/login.html``. If
you're OK with using the projectroles login template, the file can consist of
the following line:

.. code-block:: django

    {% extends 'projectroles/login.html' %}

If you intend to use projectroles templates for user management, you can delete
other existing files within the directory.


URL Configuration
=================

In the Django URL configuration file, usually found in ``config/urls.py``, add
the following lines under ``urlpatterns`` to include projectroles URLs in your
site.

.. code-block:: python

    urlpatterns = [
        # ...
        url(r'api/auth/', include('knox.urls')),
        url(r'^project/', include('projectroles.urls')),
    ]

If you intend to use projectroles views and templates as the basis of your site
layout and navigation (which is recommended), also make sure to set the site's
home view accordingly:

.. code-block:: python

    from projectroles.views import HomeView

    urlpatterns = [
        # ...
        url(r'^$', HomeView.as_view(), name='home'),
    ]

Finally, make sure your login and logout links are correctly linked. You can
remove any default allauth URLs if you're not using it.

.. code-block:: python

    from django.contrib.auth import views as auth_views

    urlpatterns = [
        # ...
        url(r'^login/$', auth_views.LoginView.as_view(
            template_name='users/login.html'), name='login'),
        url(r'^logout/$', auth_views.logout_then_login, name='logout'),
    ]


Base Template for Your Django Site
==================================

In order to make use of Projectroles views and templates, you should set the
base template of your site accordingly in ``{SITE_NAME}/templates/base.html``.

For a supported example, see ``projectroles/base_site.html``. It is strongly
recommended to use this as the base template for your site, either by extending
it or copying the content into ``{SITE_NAME}/templates/base.html`` and modifying
it to suit your needs.

If you do not need to make any modifications, the most simple way is to replace
the content of the ``{SITE_NAME}/templates/base.html`` file with the following
line:

.. code-block:: django

    {% extends 'projectroles/base_site.html' %}

.. note::

    CSS and Javascript includes in ``site_base.html`` are **mandatory** for
    Projectroles-based views and functionalities.

.. note::

    The container structure defined in the example base.html, along with
    including the ``{STATIC}/projectroles/css/projectroles.css`` are
    **mandatory** for Projectroles-based views to work without modifications.


All Done!
=========

After following all the instructions above, you should have a working Django
site with Projectroles access control and support for SODAR app. To test the
site locally execute the supplied shortcut script:

.. code-block:: console

    $ ./run.sh

Or, run the standard Django ``runserver`` command:

.. code-block:: console

    $ ./manage.py runserver

You can now browse your site locally at ``http://127.0.0.1:8000``. You are
expected to log in to view the site. Use e.g. the superuser account you created
when setting up your cookiecutter-django site.

You can now continue on to create apps or modify your existing apps to be
compatible with the SODAR Core framework. See the
:ref:`development section <development>` for app development guides. Also see the
:ref:`customization documentation <app_projectroles_custom>` for tips for
modifying the default appearance of SODAR Core.
