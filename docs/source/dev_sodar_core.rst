.. _dev_sodar_core:


SODAR Core Development
^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for development of the SODAR
Core package.


Repository Contents
===================

In addition to the apps which will be installed by the package, the following
directories are included in the repository for development use and as examples:

- **config**: Example Django site configuration
- **docs**: Usage and development documentation
- **example_backend_app**: Example SODAR Core compatible backend app
- **example_project_app**: Example SODAR Core compatible project app
- **example_site**: Example SODAR Core based Django site for development
- **example_site_app**: Example SODAR Core compatible site-wide app
- **requirements**: Requirements for SODAR Core and development
- **utility**: Setup scripts for development


Installation
============

Instructions on how to install a local development version of SODAR Core are
detailed here. Ubuntu 16.04 LTS (Xenial) is the supported OS at this time.
Later Ubuntu versions and Centos 7 have also been proven to to work, but some
system dependencies may vary for different OS versions or distributions.

Installation and development should be possible on most recent versions of
Linux, Mac and Windows, but this may require extra work and your mileage may
vary.

If you need to set up the accompanying example site in Docker, please see online
for up-to-date Docker setup tutorials for Django related to your operating
system of choice.

System Installation
-------------------

First you need to install OS dependencies, PostgreSQL 9.6 and Python3.6.

.. code-block:: console

    $ sudo utility/install_os_dependencies.sh
    $ sudo utility/install_python.sh
    $ sudo utility/install_postgres.sh

Database Setup
--------------

Next you need to setup the database and postgres user. You'll be prompted to
enter a database name, a username and a password.

.. code-block:: console

    $ sudo utility/setup_database.sh

You have to set the database URL and credentials for Django in the environment
variable ``DATABASE_URL``. For development it is recommended to place
environment variables in file ``.env`` located in your project root. To enable
loading the file in Django, set ``DJANGO_READ_DOT_ENV_FILE=1`` in your
environment variables when running SODAR or any of its management commands.
See ``config/settings/base.py`` for more information and the ``env.example``
file for an example environment file.

Example of the database URL variable as set within an ``.env`` file:

.. code-block:: console

    DATABASE_URL=postgres://sodar_core:sodar_core@127.0.0.1/sodar_core

Project Setup
-------------

Clone the repository, setup and activate the virtual environment. Once in
the environment, install Python requirements for the project:

.. code-block:: console

    $ git clone https://github.com/bihealth/sodar_core.git
    $ cd sodar_core
    $ pip install virtualenv
    $ virtualenv -p python3.6 .venv
    $ source .venv/bin/activate
    $ utility/install_python_dependencies.sh

LDAP Setup (Optional)
---------------------

If you will be using LDAP/AD auth on your site, make sure to also run:

.. code-block:: console

    $ sudo utility/install_ldap_dependencies.sh
    $ pip install -r requirements/ldap.txt

Final Setup
-----------

Initialize the database (this will also synchronize django-plugins):

.. code-block:: console

    $ ./manage.py migrate

Create a Django superuser for the example_site:

.. code-block:: console

    $ ./manage.py createsuperuser

Now you should be able to run the server:

.. code-block:: console

    $ make serve


App Development
===============

Guidelines for developing **internal** SODAR Core apps (ones included when
installing the django-sodar-core package) are detailed in this section.

REST API Views
--------------

For internal SODAR Core apps, you need to use core counterparts to the mixins
than provided for SODAR Core using sites. The counterparts use different media
type and versioning from views to be implemented on external sites. This is to
prevent version number clashes requiring changes in external APIs. The classes
can be found in ``projectroles.views_api`` and are as follows:

- ``CoreAPIVersioning``
- ``CoreAPIRenderer``
- ``CoreAPIBaseMixin``
- ``CoreAPIBaseProjectMixin``
- ``CoreAPIGenericProjectMixin``

For detailed API descriptions, see docstrings in the ``view_api`` module. The
media type and versioning for these views are **hardcoded** and should not be
changed, except version information upon a new release of SODAR Core.


Projectroles App Development
============================

This section details issues regarding updates to the ``projectroles`` app.

.. warning::

    As all other apps in SODAR Core as well as sites implementing SODAR Core
    are based on projectroles, changes to this app need to be implemented and
    tested with extra care. Also make sure to provide detailed documentation for
    all breaking changes.

Projectroles App Settings
-------------------------

Projectroles defines its own app settings in ``projectroles/app_settings.py``.
These are not expected to be altered by SODAR Core based sites. These settings
add the ``local`` attribute, which allows/disallows editing the value on a
``TARGET`` site.

To alter projectroles app settings when developing the app, update the
``PROJECTROLES_APP_SETTINGS`` dictionary as follows:

.. code-block:: python

     'example_setting': {
         'scope': 'PROJECT',  # PROJECT/USER
         'type': 'STRING',  # STRING/INTEGER/BOOLEAN
         'default': 'example',
         'options': ['example', 'example2'],  # Optional, only for settings of type STRING or INTEGER
         'label': 'Project setting',  # Optional, defaults to name/key
         'placeholder': 'Enter example setting here',  # Optional
         'description': 'Example project setting',  # Optional
         'user_modifiable': True,  # Optional, show/hide in forms
         'local': False,  # Allow editing in target site forms if True
     }


Testing
=======

To run unit tests, you have to install the headless Chrome driver (if not yet
present on your system), followed by the Python test requirements:

.. code-block:: console

    $ sudo utility/install_chrome.sh
    $ pip install -r requirements/test.txt

Now you can run all tests with the following make command:

.. code-block:: console

    $ make test

If you want to only run a certain subset of tests, use e.g.:

.. code-block:: console

    $ make test arg=projectroles.tests.test_views

For running tests with SODAR Taskflow (not currently publicly available), you
can use the supplied make command:

.. code-block:: console

    $ make test_taskflow


Remote Site Development
=======================

For developing remote site features, you will want to run two or more SODAR Core
example sites concurrently: one ``SOURCE`` site and one or more ``TARGET``
sites.

For running a single ``TARGET`` site in addition to the main site, the fastest
way to get started is the following:

First, set up a second database called ``sodar_core_target`` using
``utility/setup_database.sh``.

Next, migrate the new database and create a superuser using
``make manage_target``. It is recommended to use a different admin user name
than on your ``SOURCE`` site, to help debugging.

.. code-block:: console

    $ make manage_target arg=migrate
    $ make manage_target arg=createsuperuser

Launch your site with ``make serve_target``. By default, you can access the site
at Port ``8001`` on localhost. The port can be altered by providing the
``target_port`` parameter, e.g. ``make serve_target target_port=8002``.
Management commands to the target site can be issued with the ``make manage_target``
make command.

Due to how cookies are set by Django, you currently may have to relogin when
switching to a different site on your browser. As a workaround you can launch
one of the sites in a private/incognito window or use different browsers.

If you need to create multiple target sites for testing ``PEER`` synchronization
features, make sure that you have a separate SODAR Core database for each site
and launch each site on a different port on localhost. The configuration
``local_target2.py`` is included for developing with multiple ``TARGET`` sites.