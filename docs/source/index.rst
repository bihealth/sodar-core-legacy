.. SODAR Core documentation master file, created by
   sphinx-quickstart on Thu Sep  6 14:50:08 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _manual-main:

Welcome to the SODAR Core documentation!
========================================

This documentation provides instructions for SODAR Core usage, integration and
development. SODAR Core is framework for project access control and project
application management, also including multiple optional applications for
aiding project work. SODAR Core is built on the
`Django <https://www.djangoproject.com/>`_ web framework.

**SODAR** (System for Omics Data Access and Retrieval) is a specialized system
for managing data in omics research projects, which was the origin of the
components in this package.

The **SODAR Core** package contains the core functionality for the SODAR system
along with reusable and non-domain-specific web apps. The package and its apps
can be used in any Django-based web site which wants to make use of one or more
of the following features:

- Project-based user access control
- Dynamic app content management
- Advanced project activity logging
- Small file uploading and browsing
- Managing server-side background jobs
- Caching and aggregation of data from external services
- Tracking site information and statistics

Basics of Django site setup and instructions for third party packages used are
considered out of scope for this documentation. Basic knowledge of the Django
framework is assumed. For this, please refer to the
`official Django documentation <https://docs.djangoproject.com/en/1.11/>`_
and/or docs of related third party packages.

**NOTE:** To view this document in the rendered form during development, run
``make html`` in the ``docs`` directory of the repository. You can find the
rendered HTML in ``docs/build``. You will have to install system and Python
dependencies, including ones in ``requirements/local.txt`` for this to work. See
:ref:`dev_sodar_core`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Overview <overview>
   glossary
   getting_started
   app_projectroles
   app_adminalerts
   app_bgjobs
   app_filesfolders
   app_userprofile
   app_siteinfo
   app_sodarcache
   app_taskflow
   app_timeline
   development
   breaking_changes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
