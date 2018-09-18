.. _getting_started:


Getting Started
^^^^^^^^^^^^^^^

Basic concepts of SODAR Core apps are detailed in this document.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


Repository Contents
===================

The following Django apps will be installed when including ``django-sodar-core``
in your project:

- **projectroles**: Base app for project access management and
  dynamic app content management. All other apps require the integration of
  projectroles.
- **timeline**: Project app for logging and viewing project-related activity
- **userprofile**: Site app for viewing user profiles

The following packages are included in the repository for development and
as examples:

- **config**: Example Django site configuration
- **docs**: Usage and development documentation
- **example_project_app**: Example SODAR Core compatible project app
- **example_site**: Example/development Django site
- **example_site_app**: Example SODAR Core compatible site-wide app
- **requirements**: Requirements for SODAR Core  and development
- **utility**: Setup scripts for development


Requirements
============

Major requirements for integrating projectroles and other SODAR Core apps into
your Django site and/or participating in development are listed below. For a
complete requirement list, see the ``requirements`` and ``utility`` directories
in the repository. Listed with minimum versions supported.

- Ubuntu Linux
- Library requirements (see utility package or your cookiecutter-django site)
- Python 3.5
- Django 1.11.x (**NOTE:** 2.x not currently supported)
- PostgreSQL 9.4 and psycopg2
- Bootstrap 4.1.1
- JQuery 3.2.1
- Shepherd 1.8.1 with Tether 1.4.4
- Clipboard.js 2.0.0
- DataTables 1.10.18 with JQuery UI, FixedColumns, FixedHeader, Buttons,
  KeyTables

For more detailed instructions on what to install for local development, see
:ref:`dev_sodar_core`.


Next Steps
==========

To proceed with using the SODAR Core framework in your Django site, you must
first install and integrated the ``projectroles`` app. See the
:ref:`projectroles app documentation <app_projectroles>` for instructions.

Once projectroles has been integrated into your site, you may proceed in
installing other apps as needed.
