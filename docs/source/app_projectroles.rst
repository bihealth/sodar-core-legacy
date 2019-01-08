.. _app_projectroles:


Projectroles App
^^^^^^^^^^^^^^^^

The ``projectroles`` app is the base app for building a SODAR Core based Django
site. It provides a framework for project access management, dynamic content
including with django-plugins, models and tools for SODAR-compatible apps plus a
default template and CSS layout.

Other Django apps which intend to use aforementioned functionalities depend on
projectroles. While inclusion of other SODAR Core apps can be optional, having
projectroles installed is **mandatory** for working with the SODAR project and
app structure.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   Basics <app_projectroles_basics>
   Integration <app_projectroles_integration>
   Settings <app_projectroles_settings>
   Usage <app_projectroles_usage>
   Customization <app_projectroles_custom>
