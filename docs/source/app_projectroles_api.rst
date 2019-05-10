.. _app_projectroles_api:


Projectroles API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains API documentation for the ``projectroles`` app. Included
are functionalities and classes intended to be used by other applications.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


Plugins
=======

SODAR plugin point definitions and helper functions for plugin retrieval are
detailed in this section.

.. automodule:: projectroles.plugins
    :members:


Models
======

Projectroles models are used by other apps for project access and metadata
management as well as linking objects to projects.

.. automodule:: projectroles.models
    :members:


App Settings
============

Projectroles provides helper functions for getting or setting project and user
specific settings.

.. automodule:: projectroles.app_settings
    :members:


Common Template Tags
====================

These tags can be included in templates with
``{% load 'projectroles_common_tags' %}``.

.. automodule:: projectroles.templatetags.projectroles_common_tags
    :members:


Utilities
=========

General utility functions are stored in ``utils.py``.

.. automodule:: projectroles.utils
    :members:
