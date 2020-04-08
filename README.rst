SODAR Core
^^^^^^^^^^

.. image:: https://travis-ci.org/bihealth/sodar_core.svg?branch=master
    :target: https://travis-ci.org/bihealth/sodar_core

.. image:: https://api.codacy.com/project/badge/Grade/404e8515825548b1aa5a44dbe3d45ece
    :target: https://www.codacy.com/app/bihealth/sodar_core

.. image:: https://img.shields.io/badge/License-MIT-green.svg
    :target: https://opensource.org/licenses/MIT

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

.. image:: https://readthedocs.org/projects/sodar-core/badge/?version=latest
    :target: https://sodar-core.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://zenodo.org/badge/165220058.svg
    :target: https://zenodo.org/badge/latestdoi/165220058

SODAR Core is a framework for Django web application development. It was
conceived to facilitate the creation of scientific data management and
analysis web applications (but can be useful in other contexts as well).


Quickstart
==========

SODAR Core can only be used from within Django projects.  The easiest way to
start out is following the `For the Impatient
<https://sodar-core.readthedocs.io/en/latest/for_the_impatient.html>`__
section in our documentation.


Introduction
============

The SODAR Core repository containes reusable and non-domain-specific apps making
up the base of the SODAR system. These apps can be used for any Django
application which wants to make use of the following features:

- Project-based user access control
- Dynamic app content management
- Advanced project activity logging
- Small file uploading and browsing
- Managing server-side background jobs
- Caching and aggregation of data from external services
- Tracking site information and statistics
- API token management

This repository provides the following installable Django apps:

- **projectroles**: Base app for project access management and
  dynamic app content management. All other apps require the integration of
  projectroles.
- **adminalerts**: Site app for displaying site-wide messages to all users.
- **bgjobs**: Project app for managing background jobs.
- **filesfolders**: Storage and management of small files.
- **siteinfo**: Site app for displaying site information and statistics for
  administrators.
- **sodarcache**: Generic caching and aggregation of data referring to external
  services.
- **taskflowbackend**: Backend app providing an API for the optional
  ``sodar_taskflow`` transaction service.
- **timeline**: Project app for logging and viewing project-related activity.
- **tokens**: Token management for API access.
- **userprofile**: Site app for viewing user profiles.

Also included are resources and examples for developing SODAR compatible apps.


Installation
============

The ``django-sodar-core`` package can be installed from GitHub as follows. PyPI
installation is forthcoming.

.. code-block:: console

    pip install -e git+https://github.com/bihealth/sodar_core.git@v0.8.0#egg=django-sodar-core

Please note that This package installs a collection Django apps to
be used in a Django web site project. See
`SODAR Core documentation <https://sodar-core.readthedocs.io/en/latest/?badge=latest>`_
for detailed documentation on use, integration and development.
