SODAR Core
^^^^^^^^^^

.. image:: https://badge.fury.io/py/django-sodar-core.svg
    :target: https://badge.fury.io/py/django-sodar-core

.. image:: https://github.com/bihealth/sodar-core/workflows/build/badge.svg
    :target: https://github.com/bihealth/sodar-core/actions?query=workflow%3ABuild

.. image:: https://app.codacy.com/project/badge/Grade/77c0057a041f4e0c9a0bfc79e9023e04
    :target: https://www.codacy.com/app/bihealth/sodar-core/dashboard

.. image:: https://app.codacy.com/project/badge/Coverage/77c0057a041f4e0c9a0bfc79e9023e04
    :target: https://www.codacy.com/gh/bihealth/sodar-core/dashboard

.. image:: https://img.shields.io/badge/License-MIT-green.svg
    :target: https://opensource.org/licenses/MIT

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

.. image:: https://readthedocs.org/projects/sodar-core/badge/?version=latest
    :target: https://sodar-core.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.4269346.svg
    :target: https://doi.org/10.5281/zenodo.4269346

SODAR Core is a framework for Django web application development.

It was conceived to facilitate the creation of scientific data management and
analysis web applications, but can be useful in other contexts as well.
In that it is similar to the CMS or ecommerce frameworks that you can find
`Awesome Django List <https://github.com/wsvincent/awesome-django#content-management-systems>`__ but you will find the components/libraries provided in SODAR Core are more generic and in this reflecting the broader range of applications that we target.


Examples / See It In Action
===========================

SODAR Core is a framework for developing Django web applications. The following
data management and analysis web applications are based on SODAR Core and have
been made available as open source:

- **SODAR** is the system for Omics data access and retrieval. It is used to
  model study metadata and manage associated data files in different Omics
  research projects. SODAR Core was created by separating re-usable research
  project management components from the SODAR project. The source code of SODAR
  can be found on `github.com/bihealth/sodar-server <https://github.com/bihealth/sodar-server>`__.
- **VarFish** is a web-based tool for the analysis of variants.
  It showcases how to build a complex data warehousing and data analysis web
  appliction using SODAR Core.
  More details are described in the `NAR Web Server Issue publication (doi:10.1093/nar/gkaa241) <https://doi.org/10.1093/nar/gkaa241>`__.
  The source code can be found on `github.com/bihealth/varfish-server <https://github.com/bihealth/varfish-server>`__.
  A demo is available at `varfish-demo.bihealth.org <https://varfish-demo.bihealth.org/login/>`__.
- **Digestiflow** is a web-based data system for the management and
  demultiplexing of Illumina Flow Cells. It further implements various tools for
  sanity checking Illumina sample sheets and quality control (e.g., comparing
  barcode adapter sequence and actual sequence present in the sequencer output).
  You can find out more in our publication in `Bioinformatics (doi:10.1093/bioinformatics/btz850) <https://doi.org/10.1093/bioinformatics/btz850>`__.
  The source code can be found on `github.com/bihealth/digestiflow-server <https://github.com/bihealth/digestiflow-server>`__.
- **Kiosc** is a web application that allows to build scheduler Docker
  containers for "data science" apps and dashboards.
  You can find the source code on `github.com/bihealth/kiosc <https://github.com/bihealth/kiosc>`__.


Quickstart
==========

SODAR Core can only be used from within Django projects. The easiest way to
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
- **appalerts**: Site app and backend for raising alerts to users from apps.
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

The ``django-sodar-core`` package can be installed into your Django project
from PyPI as follows. Note that it is strongly recommended to freeze the
dependency to a specific version, as this package is under active development
and breaking changes are possible.

.. code-block:: console

    pip install django-sodar-core==0.10.9

For installing a development version you can point your dependency to a specific
commit ID in GitHub. Note that these versions may not be stable.

.. code-block:: console

    pip install -e git+https://github.com/bihealth/sodar-core.git@xxxxxxxxxxxxx#egg=django-sodar-core

Please note that This package installs a collection of Django apps to be used in
a Django web site project. See
`SODAR Core documentation <https://sodar-core.readthedocs.io/en/latest/?badge=latest>`_
for detailed documentation on use, integration and development.


Repository
==========

The branches of the SODAR Core repository are organized as follows:

- ``main``: The latest stable release.
- ``dev``: The current development branch. Most recent features go here, but
  stability is not guaranteed.

When including SODAR Core in your Django project, it is highly recommended to
freeze your dependency to a specific release tag or commit ID. The project is
under development and breaking changes may be introduced frequently.

Contributions should always be based on the ``dev`` branch.
