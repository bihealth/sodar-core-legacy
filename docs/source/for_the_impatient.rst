.. _for_the_impatient:

For the Impatient
^^^^^^^^^^^^^^^^^

This section will give you the essential steps to setup a new SODAR Core based project.
We will link to the parts of the manual where they were taken from such that you can read more in depth there.

.. _for_the_impatient_see_it_in_action:

See It In Action
================

We have developed the following data management and analysis web applications using SODAR-core.
Although there only is a public demo available for VarFish at this time, the source code of the applications demonstrate how to use SODAR-core in complex web applications.

  `VarFish <https://github.com/bihealth/varfish-server>`__
    is a web-based tool for the analysis of variants.
    It showcases how to build a complex data warehousing and data analysis web appliction using SODAR-Core.
    More details are described in the `NAR Web Server Issue publication (doi:10.1093/nar/gkaa241) <https://doi.org/10.1093/nar/gkaa241>`__.
    The source code can be found on `github.com/bihealth/varfish-server <https://github.com/bihealth/varfish-server>`__.
    A demo is available at `varfish-demo.bihealth.org <https://varfish-demo.bihealth.org/login/>`__.

  `DigestiFlow <https://github.com/bihealth/digestiflow-server>`__
    is a web-based data system for the management and demultiplexing of Illumina Flow Cells.
    It further implements various tools for sanity checking Illumina sample sheets and quality control (e.g., comparing barcode adapter sequence and actual sequence present in the sequencer output).
    You can find out more in our publication in `Bioinformatics (doi:10.1093/bioinformatics/btz850) <https://doi.org/10.1093/bioinformatics/btz850>`__.
    The source code can be found on `github.com/bihealth/digestiflow-server <https://github.com/bihealth/digestiflow-server>`__.
    There currently is no public demo instance yet.

  `Kiosc <https://github.com/bihealth/kiosc>`__
    is a web application that allows to build scheduler Docker containers for "data science" apps and dashboards.
    There currently is no public demo instance yet.

Prerequisites
=============

Linux / Mac
    We use bash syntax on a Unix system and assume that you can adjust this to your system when needed.

PostgreSQL
    Please install version 9.6 or above.
    We assume that you have access to the ``postgres`` user or some other administrative user.

Development Essentials
    We assume that you have ``git``, Python 3.6, and other essential tools installed.
    If you are using a mainstream Unix-like distribution (Mac qualifies) then you should be good to go.

.. info:

    In the case that you get an error as follows when installing the dependencies, make sure that you have the development libraries of postgres installed.
    E.g., on Debian-based systems install ``postgresql-dev``, for Red Hat and CentOS install ``postgresql-devel``.

    ::

        Error: pg_config executable not found.


Isolate Python Environment
==========================

If you use `virtualenv <https://docs.python-guide.org/dev/virtualenvs/>`_ then please create a new virtual environment for the project and activate it.
Otherwise, follow the previous link and do this now or you can follow along us using `conda <https://www.google.com/search?client=ubuntu&channel=fs&q=conda&ie=utf-8&oe=utf-8>`_.

The following creates a new Miniconda installation on 64 bit Linux or Mac.
The `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ website has URLs to more.

.. code-block:: bash

    # Linux
    $ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    $ bash Miniconda3-latest-Linux-x86_64.sh -b -p ~/miniconda3
    $ source ~/miniconda3/bin/activate
    $ conda install -y python=3.7

    # Mac
    $ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
    $ bash Miniconda3-latest-MacOSX-x86_64.sh -b -p ~/miniconda3
    $ source ~/miniconda3/bin/activate
    $ conda install -y python=3.7

For activating the conda installation, use ``source ~/miniconda3/bin/activate``.

Install SODAR-Core
==================

We simply use ``pip`` for this:

.. code-block:: bash

    # you must have your miniconda3 install sourced, skip if done already
    $ source ~/miniconda3/bin/activate
    $ pip install -e git+https://github.com/bihealth/sodar_core.git@v0.8.4#egg=django-sodar-core

Download Example Site
=====================

We maintain a Git repository with a django project using the latest SODAR Core version here on GitHub: `sodar_django_site <https://github.com/bihealth/sodar_django_site>`_.
We will use this to get hit the ground running.
See :ref:`app_projectroles_integration` on other ways to get started with SODAR Core.

.. code-block:: bash

    $ git clone https://github.com/bihealth/sodar_django_site.git  sodar_django_site
    $ cd sodar_django_site

From here on, we assume that you are located (a) within the ``sodar_django_site`` directory and (b) have done ``source ~/miniconda3/bin/activate`` such that ``which python`` shows ``~/miniconda3/bin/python``.

To complete this step install the development requirements.

.. code-block:: bash

    $ pip install -r requirements/local.txt

Configure Environment
=====================

The next step is to perform some configuration.
SODAR Core is built on the `12 factor app <https://12factor.net/>`_ principles.
Configuration is done using environment variables.
For development, they are read from the ``.env`` file in your ``sodar_django_site`` checkout.
We are shipping an example setting file that you should copy and then edit.

.. code-block:: bash

    $ cp env.example .env
    # now edit .env

To start out, it will be sufficient to make sure you can connect to the database.
The default value for this is shown below.

.. code-block:: bash

    DATABASE_URL="postgres://sodar_django_site:sodar_django_site@127.0.0.1/sodar_django_site"

To keep it simple, you can use the following commands to create the correct database, user, and set the password.

.. code-block:: bash

    $ sudo -u postgres createuser -ds sodar_django_site -W
    [sudo] password for USER: <enter your password>
    Password: <enter: sodar_django_site>
    $ sudo -u postgres createdb --owner=sodar_django_site sodar_django_site

Now, we have to make sure that the environment file is read:

.. code-block:: bash

    $ sed -ie "s/^READ_DOT_ENV_FILE.*/READ_DOT_ENV_FILE = env.bool('DJANGO_READ_DOT_ENV_FILE', default=True)/" config/settings/base.py

Database Initialization
=======================

For the final steps, you will initialize the database...

.. code-block:: bash

    $ python manage.py migrate

... and create a new admin user ...

.. code-block:: bash

    $ python manage.py createsuperuser
    Username: root
    Email address: root@example.com
    Password:
    Password (again):
    Superuser created successfully.

The First Login
===============

Now, start the server, and you can then visit http://127.0.0.1:8000/login/?next=/

.. code-block:: bash

    $ python manage.py runserver
    Performing system checks...

    System check identified no issues (0 silenced).
    February 03, 2020 - 10:00:53
    Django version 1.11.25, using settings 'config.settings.local'
    Starting development server at http://127.0.0.1:8000/
    Quit the server with CONTROL-C.

You should see the following:

.. figure:: _static/figures/impatient_login_screen.png

Now, login with your superuser and you should see the following:

.. figure:: _static/figures/impatient_project_list.png

Click the little user icon on the top right to access the django admin (here is where you can create more users, for example) but also the preconfigured :term:`Site Apps <Site App>` :ref:`adminalerts <app_adminalerts>`, :ref:`siteinfo <app_siteinfo>`, :ref:`userprofile <app_userprofile>` and configuration for remote sites.
The plus button on the left allows to create new categories and projects.

Now might also be a good time to read up more on the :ref:`projectroles <app_projectroles>` app as this is the fundamental app for most further development.

The First Project
=================

You cannot create projects on the root level but you have to create a new category first (collections of projects).
Use the "create category" button on the left to create a "example category" first, then create an "example project" within.
The project details view should look as follows.

.. figure:: _static/figures/impatient_project_home.png

Note that the site search already works, so typing "example" into the text field on the top and clicking "search" will return your example project.
The project overview shows the "project home card" for the installed project apps filefolders, timeline, and bgjobs.
Usually, the latest five entries are shown here.

.. note::

    The filesfolders app is an example of the **data management** application of SODAR Core based apps.
    You can easily imagine a more advanced module/app that not only allows tagging of files but more structuring data and meta data more strongly.
    Actually, SODAR Core was extracted as a re-useable library of component from our (not yet released) SODAR project that allows the management of structured meta data of experiments and files with data from such experiments.

Go ahead and try out the filesfolders app by clicking the "small files" icon on the left.
After creating folders and uploading a few files, you will see a trace of actions in the timeline app:

.. figure:: _static/figures/impatient_timeline.png

.. note::

    By default, ``sodar_django_site`` will store the files in the PostgreSQL database but you can easily configure it to use other storage backends, e.g., the S3 protocol, with the `django-storage <https://django-storages.readthedocs.io/en/latest/>`_ package but this goes beyond this documentation.

Also, you will be able to find your uploaded file by name through the search box.
Note that any app that you write can easily provide all the integrations with the SODAR Core framework (your apps are no different than the built-in ones).
Just have a look how we did it in the apps shipping with SODAR Core.

Summary
=======

Here is a quick summary on how SODAR Core interacts with the built-in and user apps:

- At the lower most level all content is managed in projects which themselves can be assigned into categories.
- Project apps can provide new content types that can be put into projects.
  For example, the filesfolders app allows you to store files, folders, and assign meta data to them.
  As another example, the timelines app stores events that occured in a project, and other apps such as the filesfolders app can register their events with it.
- SODAR Core defines several plugin extension points that your apps can implement and make their content findable, for example.
- Site apps allow to provide features independent of a project.
  For example, the userprofile app allows to access user settings and the adminalerts app allows to post global notifications.

Going on From Here
==================

- You can now start exploring your ``sodar_django_site`` and play around with it.
- You can read the :ref`user_stories` section to learn how SODAR Core based applications are built.
- Continue reading :ref:`getting_started` for a more comprehensive documentation and walk-through of SODAR Core and its apps.
- Have a look at the web apps developed by us that are using SODAR Core as shown in the :ref:`for_the_impatient_see_it_in_action` section.
