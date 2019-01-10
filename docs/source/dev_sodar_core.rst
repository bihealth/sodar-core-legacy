.. _dev_sodar_core:


SODAR Core Development
^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for development of the SODAR
Core package.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


Installation
============

Instructions on how to install a local development version of SODAR Core.
Ubuntu 16.04 LTS (Xenial) is the supported OS at this time. System dependencies
may vary for different OS versions or distributions.

System Library Installation
---------------------------

First you need to install OS dependencies, PostgreSQL 9.6 and Python3.6.

.. code-block:: console

    $ sudo utility/install_os_dependencies.sh
    $ sudo utility/install_python.sh
    $ sudo utility/install_postgres.sh

Database Setup
--------------

Create a PostgreSQL user and a database for your application. In the example,
we use ``sodar_core`` for the database, user name and password. Make sure to
give the user the permission to create further PostgreSQL databases (used for
testing).

.. code-block:: console

    $ sudo su - postgres
    $ psql
    $ CREATE DATABASE sodar_core;
    $ CREATE USER sodar_core WITH PASSWORD 'sodar_core';
    $ GRANT ALL PRIVILEGES ON DATABASE sodar_core to sodar_core;
    $ ALTER USER sodar_core CREATEDB;
    $ \q

You have to add the credentials in the environment variable ``DATABASE_URL``.
For development it is recommended to place this variable in an ``.env`` file and
set ``DJANGO_READ_DOT_ENV_FILE=1`` in your actual environment. See
``config/settings/base.py`` for more information.

.. code-block:: console

    $ export DATABASE_URL='postgres://sodar_core:sodar_core@127.0.0.1/sodar_core'

Project Setup
-------------

Clone the repository, setup and activate the virtual environment. Once in
the environment, install Python requirements for the project:

.. code-block:: console

    $ git clone git+https://github.com/bihealth/sodar_core.git
    $ cd sodar_core
    $ pip install virtualenv
    $ virtualenv -p python3.6 .venv
    $ source .venv/bin/activate
    $ pip install -r requirements/local.txt

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

    $ ./run.sh


Testing
=======

To run unit tests, you have to install the headless Chrome driver (if not yet
present on your system), followed by the Python test requirements:

.. code-block:: console

    $ sudo utility/install_chrome.sh
    $ pip install -r requirements/test.txt

Now you can run all tests with the following script:

.. code-block:: console

    $ ./test.sh

If you want to only run a certain subset of tests, use e.g.:

.. code-block:: console

    $ ./test.sh projectroles.tests.test_views

For running tests with SODAR Taskflow (not currently publicly available), you
can use the supplied shortcut script:

.. code-block:: console

    $ ./test_taskflow.sh


Contributing
============

SODAR Core is currently in active development in a private BIH repository. The
public GitHub repository is primarily intended for publishing stable releases.
Furthermore, the issue IDs within the code and documentation point to our
private issue tracker unless otherwise mentioned.
