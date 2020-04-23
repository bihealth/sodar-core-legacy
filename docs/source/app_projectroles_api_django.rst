.. _app_projectroles_api_django:


Projectroles Django API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the Django API documentation for the ``projectroles``
app. Included are functionalities and classes intended to be used by other
applications when building a SODAR Core based Django site.


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

Projectroles provides an API for getting or setting project and user
specific settings.

.. autoclass:: projectroles.app_settings.AppSettingAPI
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


Base REST API View Classes
==========================

Base view classes and mixins for building REST APIs can be found in
``projectroles.views_api``.

.. currentmodule:: projectroles.views_api

Permissions / Versioning / Rendering
------------------------------------

.. autoclass:: SODARAPIProjectPermission
    :members:
    :show-inheritance:

.. autoclass:: SODARAPIVersioning
    :members:
    :show-inheritance:

.. autoclass:: SODARAPIRenderer
    :members:
    :show-inheritance:

Base API View Mixins
--------------------

.. autoclass:: SODARAPIBaseMixin
    :members:

.. autoclass:: SODARAPIBaseProjectMixin
    :members:
    :show-inheritance:

.. autoclass:: APIProjectContextMixin
    :members:
    :show-inheritance:

.. autoclass:: SODARAPIGenericProjectMixin
    :members:
    :show-inheritance:

.. autoclass:: ProjectQuerysetMixin
    :members:


Base Ajax API View Classes
==========================

Base view classes and mixins for building Ajax API views can be found in
``projectroles.views_ajax``.

.. currentmodule:: projectroles.views_ajax

.. autoclass:: SODARBaseAjaxView
    :members:
    :show-inheritance:

.. autoclass:: SODARBasePermissionAjaxView
    :members:
    :show-inheritance:

.. autoclass:: SODARBaseProjectAjaxView
    :members:
    :show-inheritance:


Base Serializers
================

Base serializers for SODAR Core compatible models are available in
``projectroles.serializers``.

.. currentmodule:: projectroles.serializers

.. autoclass:: SODARModelSerializer
    :members:
    :show-inheritance:

.. autoclass:: SODARProjectModelSerializer
    :members:
    :show-inheritance:

.. autoclass:: SODARNestedListSerializer
    :members:
    :show-inheritance:

.. autoclass:: SODARUserSerializer
    :members:
    :show-inheritance:
