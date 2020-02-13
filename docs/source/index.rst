.. _manual_main:

Welcome to the SODAR Core documentation!
========================================

SODAR Core is a framework for `Django <https://www.djangoproject.com/>`_ web
application development. It was conceived to facilitate the creation of
**scientific data management** and analysis web applications (but can be
useful in other contexts as well).

How to read this manual?
------------------------

There is two ways:

Front to Back
  If you have the time and patience, reading the whole manual will teach
  you everything.

Jump Around (recommended)
  Start with :ref:`for_the_impatient`, skim over the summary of each app, and
  explore what interests you most.

What's inside SODAR Core?
-------------------------

The full list of apps are shown in the table of contents (on the left if you
are reading the HTML version of this documentation) and here are some
highlights:

- Project-based user access control
- Dynamic app content management
- Advanced project activity logging
- Small file uploading and browsing
- Managing server-side background jobs
- Caching and aggregation of data from external services
- Tracking site information and statistics

What's inside this documentation?
---------------------------------

Overview & Getting Started
  This part aims at getting you an birds-eye view of SODAR Core and its usage.

SODAR Core Apps
  This part documents each Django app that ships with SODAR. As
  a reminder, in Django development, *apps* are re-useable modules with code
  for supporting a certain use case.

Project Info
  This part of the documentation provides meta information about the project
  and the full changelog.

What's not inside this documentation?
-------------------------------------

You should know the following before this documentation is useful to you:

Python Programming
  There's tons of documentation on the internet but the `official Python
  documentation <https://docs.python.org/3/>`_ is a good starting point as
  any.

Django Development
  For learning about Django, head over to the `excellent documentation of the
  Django Project <https://docs.djangoproject.com/en/1.11/>`_.

HTML / Javascript / CSS / Bootstrap 4
  Together with Django, SODAR Core provides a framework to plug in your own
  HTML and related front-end code. We assume that you have web development
  experience and in particular know your way around Bootstrap 4.

  We're using the Bootstrap 4 CSS framework and you can learn about it in many
  places including `the official documentation
  <https://getbootstrap.com/docs/4.3/getting-started/introduction/>`_

.. note::

   You can find the official version of this documentation at
   `readthedocs.io <https://sodar-core.readthedocs.io/en/latest/>`_.
   If you view these files on GitHub, beware that their renderer does not
   render the ReStructuredText files correctly and content may be missing.

.. toctree::
    :caption: Overview & Getting started
    :name: overview_getting_started
    :hidden:
    :titlesonly:

    Overview <overview>
    getting_started
    for_the_impatient

.. toctree::
    :maxdepth: 2
    :caption: SODAR Core Apps
    :name: sodar_core_apps
    :hidden:
    :titlesonly:

    app_projectroles
    app_adminalerts
    app_bgjobs
    app_filesfolders
    app_userprofile
    app_siteinfo
    app_sodarcache
    app_taskflow
    app_timeline
    app_tokens

.. toctree::
    :maxdepth: 2
    :caption: Project Info
    :name: project_info
    :hidden:
    :titlesonly:

    contributing
    code_of_conduct
    glossary
    development
    major_changes
    Full Changelog <changelog>

Indices and tables
==================

* :ref:`modindex`
* :ref:`genindex`
* :ref:`search`
