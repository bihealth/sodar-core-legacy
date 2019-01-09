.. _dev_sodar_core:


SODAR Core Development
^^^^^^^^^^^^^^^^^^^^^^

.. warning::

   Under construction!

This document details instructions and guidelines for development of the SODAR
Core package.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.

**TODO:** Add alternate instructions if installing things under e.g. conda?


Installation
============

Instructions on how to install the repo for developing SODAR Core itself.

Database Setup
--------------

First, create a postgresql user and a database for your application.
For example, use ``sodar_core`` for the database, user name and password.
Also, make sure to give the user the permission to create further Postgres
databases (used for testing).

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
set ``DJANGO_READ_DOT_ENV_FILE`` to True in your actual environment. See
``config/settings/base.py`` for more information.

.. code-block:: console

    $ export DATABASE_URL='postgres://sodar_core:sodar_core@127.0.0.1/sodar_core'

Virtualenv Setup
----------------

Clone the repository and setup the virtual environment inside:

.. code-block:: console

    $ git clone git+https://github.com/bihealth/sodar_core.git
    $ cd sodar_core
    $ virtualenv -p python3.6 .venv
    $ source .venv/bin/activate

System Library Installation
---------------------------

Install the dependencies:

.. code-block:: console

    $ sudo utility/install_os_dependencies.sh install
    $ sudo utility/install_chrome.sh
    $ pip install --upgrade pip
    $ utility/install_python_dependencies.sh install

If you are using LDAP/AD, make sure to also run:

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
present on your system):

.. code-block:: console

    $ sudo utility/install_chrome.sh

Now you can run all tests with the following script:

.. code-block:: console

    $ ./test.sh

If you want to only run a certain subset of tests, use e.g.:

.. code-block:: console

    $ ./test.sh projectroles.tests.test_views


Contributing
============

SODAR Core is currently in active development in a private BIH repository. The
public GitHub repository is primarily intended for publishing stable releases.
Furthermore, the issue IDs within the code and documentation point to our
private issue tracker unless otherwise mentioned.
