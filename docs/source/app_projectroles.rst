.. _app_projectroles:


Projectroles App
^^^^^^^^^^^^^^^^

The ``projectroles`` app is the base app for building a
:term:`SODAR Core based Django site<SODAR Core Based Site>`. It provides a
ramework for project access management, dynamic content retrieval, models and
tools for SODAR-compatible apps plus a default template and CSS layout.

Other Django apps which intend to use aforementioned functionalities depend on
projectroles. While inclusion of other SODAR Core apps can be optional, having
projectroles installed is **mandatory** for working with the SODAR Core project
and app structure.

.. toctree::
   :maxdepth: 3
   :caption: Contents:

    Basics <app_projectroles_basics>
    Integration <app_projectroles_integration>
    Settings <app_projectroles_settings>
    Usage <app_projectroles_usage>
    Customization <app_projectroles_custom>
    REST API Documentation <app_projectroles_api_rest>
    Django API Documentation <app_projectroles_api_django>
