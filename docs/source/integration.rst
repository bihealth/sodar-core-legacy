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
   Currently, SODAR Projectroles only supports Django 1.11.x, while the latest
   versions of Cookiecutter set up Django 2.0.x by default. It is strongly
   recommended to use Django 1.11 LTS for time being. Compatibility with 2.0 and
   upwards is not guaranteed! Integration into a
   `1.11 release<https://github.com/pydanny/cookiecutter-django/releases/tag/1.11.10>`_
   of cookiecutter-django has been tested and verified to be working.

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

First, add the projectroles and djangoplugins package requirements into your
``requirements/base.txt`` file.

At the time of writing the projectroles package is in development, so it is
recommended to clone a specific commit before we reach a stable 0.1.0 release.

Add the following rows into your ``base.txt`` file:

.. code-block::
   -e git://github.com/mikkonie/django-plugins.git@1bc07181e6ab68b0f9ed3a00382eb1f6519e1009#egg=django-plugins
   -e git+ssh://git@cubi-gitlab.bihealth.org/CUBI_Engineering/CUBI_Data_Mgmt/sodar_projectroles.git@7ce3241639618ddad133d9a08621b8fe2baf0d87#egg=django-sodar-projectroles

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
follows (substitute {SITE_NAME} with the name of your site package).

.. code-block::
   import environ
   SITE_PACKAGE = '{SITE_NAME}'
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
       'projectroles.apps.ProjectrolesConfig',
       'user_profile.apps.UserprofileConfig',
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
   'projectroles.context_processors.urls_processor',

Email
-----

Under ``EMAIL_CONFIGURATION``, add the following lines:

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

Logging
-------

It is also recommended to add "projectroles" under ``LOGGING['loggers']``. For
production, INFO debug level is recommended.


LDAP/AD Configuration (optional)
--------------------------------

If you want to utilize LDAP/AD user logins as configured by projectroles, you
can add the following configuration. Make sure to also add the related env
variables to your configuration.

The following lines are **optional**. If only using one LDAP/AD server, you can
leave the "secondary LDAP server" values unset.

.. code-block::
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
       AUTH_LDAP_DOMAIN_PRINTABLE = env.str('AUTH_LDAP_DOMAIN_PRINTABLE', None)

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
               'AUTH_LDAP2_DOMAIN_PRINTABLE', None)

           AUTHENTICATION_BACKENDS = tuple(itertools.chain(
               ('projectroles.auth_backends.SecondaryLDAPBackend',),
               AUTHENTICATION_BACKENDS,))


User Configuration
==================

In order for projectroles to work, you need to extend the default user model.

Extending the User Model
------------------------

In a cookiecutter-django project, an extended user model should already exist
in ``{SITE_NAME}/users/models.py``. The abstract model provided by projectroles
provides the same model with critical additions, most notably the ``omics_uuid``
field used as an unique identifier for SODAR objects including users.

If you have not added any of your own modifications to the model, you can simply
replace the existing model extension with the following code:

.. code-block::
   from projectroles.models import OmicsUser

   class User(OmicsUser):
       pass

If you need to add your own extra fields or functions (or have existing ones
already), you can add them in this model.

After updating the user model, create and run database migrations.

.. code-block::
   $ ./manage.py makemigrations
   $ ./manage.py migrate

Note that you probably will need to edit the default unit tests under
``{SITE_NAME}/users/tests/`` for them to work. Again, you can see an example in
the ``example_site`` package of the projectroles repository.

Populating UUIDs for Existing Users
-----------------------------------

When integrating projectroles into an existing site with existing users, the
``omics_uuid`` field needs to be populated. See
`instructions in the official Django documentation<https://docs.djangoproject.com/en/1.11/howto/writing-migrations/#migrations-that-add-unique-fields>`_
on how to create the required migrations.

Synchronizing User Groups for Existing Users
--------------------------------------------

To set up groups for existing users, run the ``syncgroups`` management command.

.. code-block::
   ./manage.py syncgroups

User Profile Site App
---------------------

The ``user_profile`` site app package is installed together with projectroles.
It adds a user profile page in the user dropdown. Use of the app is not
mandatory but recommended, unless you are already using some other user profile
app.

Add Login Template
------------------

You should add a login template to ``{SITE_NAME}/templates/users/login.html``. If
you're OK with using the Projectroles login template, the file can consist of
the following line:

.. code-block::
   {% extends 'projectroles/login.html' %}

If you intend to use projectroles templates for user management, you can delete
other existing files within the directory.


URL Configuration
=================

In the Django URL configuration file, usually found in ``config/urls.py``, add
the following lines under ``urlpatterns`` to include projectroles URLs in your
site.

.. code-block::
   urlpatterns = [
       # ...
       url(r'api/auth/', include('knox.urls')),
       url(r'^project/', include('projectroles.urls')),
       url(r'^user/', include('user_profile.urls')),
   ]

If you intend to use projectroles views and templates as the basis of your site
layout and navigation (which is recommended), also make sure to set the site's
home view accordingly:

.. code-block::
   from projectroles.views import HomeView

   urlpatterns = [
       # ...
       url(r'^$', HomeView.as_view(), name='home'),
   ]

Finally, make sure your login and logout links are correctly linked. You can
remove any default allauth URLs if you're not using it.

.. code-block::
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

For a minimal example, see ``example_site/templates/base.html`` in the
projectroles repository. It is strongly recommended to copy and use this as the
base template for your site.

.. note::
   CSS and Javascript includes in the example base.html are **mandatory** for
   the Projectroles views and functionalities.

.. note::
   The container structure defined in the example base.html, along with
   including the ``STATIC/projectroles/css/project.css`` are **mandatory** for
   the Projectroles views to work without modifications.


Customizing Your Site
=====================

Here you can find some hints for customizing your site.

Project CSS
-----------

While it is strongly recommended to use the Projectroles layout and styles,
there are of course many possibilities for customization.

If some of the CSS definitions in ``STATIC/projectroles/css/project.css`` do not
suit your purposes, it is of course possible to override them in your own
includes. It is still recommended to include the *"Flexbox page setup"* section
as is.

Title Bar
---------

You can implement your own title bar by replacing the default base.html include
of ``projectroles/_site_titlebar.html`` with your own HTML or include.

When doing this, it is possible to include elements from the default title bar
separately:

- Search form: ``projectroles/_site_titlebar_search.html``
- Site app and user operation dropdown: ``projectroles/_site_titlebar_dropdown.html``

See the templates themselves for further instructions.


Site Icon
---------

An optional site icon can be placed into ``STATIC/images/logo_navbar.png`` to be
displayed in the default Projectroles title bar.

Footer
------

Footer content can be specified in ``{SITE_NAME}/templates/include/_footer.html``.
