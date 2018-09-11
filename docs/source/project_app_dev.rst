Project App Development
^^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for developing Django project
apps to be used with the Projectroles-based SODAR Core framework. This also
applies for modifying existing apps into project apps.

**NOTE:** the display of this document in Gitlab is incomplete and all listings
will be missing. Please click "display source" if you want to read this in
Gitlab.

.. hint::
   The package ``example_project_app`` in the projectroles repository provides
   a concrete minimal example of a working project app.


Project App Basics
==================

Project apps in a nutshell:

- Provide a functionality related to a project
- Are dynamically included in project views by Projectroles using plugins
- Use the project-based role and access control provided by Projectroles
- Are included in the projectroles search
- Provide an includeable element (e.g. content overview) for the project details
  page
- Appear in the project menu sidebar in the default Projectroles templates

Requirements for setting up a project app:

- Implement project relations and SODAR UUIDs in the app's Django models
- Use provided mixins, keyword arguments and conventions in views
- Extend projectroles base templates in your templates
- Implement specific templates for dynamic inclusion by Projectroles
- Implement ``plugins.py`` with definitions and function implementations
- Implement ``rules.py`` with access rules

Fulfilling these requirements is detailed further in this document.


Prerequisites
=============

This documentation assumes you have a Django project with Projectroles set up
(see ``integration.rst``). The instructions can be applied either to modify a
previously existing app, or to set up a fresh app generated normally with
``./manage.py startapp``.

It is also assumed that apps are more or less created according to best
practices defined by `Two Scoops<https://www.twoscoopspress.com/>`_, with the
use of `Class-Based Views<https://docs.djangoproject.com/en/1.11/topics/class-based-views/>`_
being a requirement.


Models
======

In order to hook up your Django models into projects, there are two
requirements.

Project ForeignKey
------------------

Add a ``ForeignKey`` field for the ``projectroles.models.Project`` model,
either called ``project`` or accessible with a ``get_project()`` function
implemented in your model.

Object UUID
-----------

To provide a unique identifier for your object in the SODAR context, add a
``UUIDField`` with the name of ``omics_uuid`` into your model.

.. note::
   Projectroles links to objects in URLs, links and forms using UUIDs instead of
   database private keys. This is strongly recommended for all Django models in
   apps using the projectroles framework.

.. note::
   When updating an existing Django model with an existing database, the
   ``omics_uuid`` field needs to be populated. See
   `instructions in the official Django documentation<https://docs.djangoproject.com/en/1.11/howto/writing-migrations/#migrations-that-add-unique-fields>`_
   on how to create the required migrations.

Model Example
-------------

Below is an example of a projectroles-compatible Django model:

.. code-block::
   import uuid
   from django.db import models
   from projectroles.models import Project

   class SomeModel(models.Model):
       some_field = models.CharField(
           help_text='Your own field')
       project = models.ForeignKey(
           Project,
           related_name='some_objects',
           help_text='Project in which this object belongs')
       omics_uuid = models.UUIDField(
           default=uuid.uuid4,
           unique=True,
           help_text='SomeModel Omics UUID')


Views
=====

Certain guidelines must be followed in developing views to utilize the
projectroles framework.

URL Keyword Arguments
---------------------

In order to link a view to project and check user permissions using mixins,
the URL keyword arguments **must** include an argument which matches *one of
the following conditions*:

- Contains a kwarg ``project`` which corresponds to the ``omics_uuid``
  member value of a ``projectroles.models.Project`` object
- Contains a kwarg corresponding to the ``omics_uuid`` of another Django
  model, which must contain a member field ``project`` which is a foreign key
  for a ``Projectroles.models.Project`` object. The kwarg **must** be named
  after the Django model of the referred object (in lowercase).
- Same as above, but corresponding to a Django model which provides a
  ``get_project()`` function which returns a ``Projectroles.models.Project``
  object.

Examples:

.. code-block::
   urlpatterns = [
       # Direct reference to a Project object
       url(
           regex=r'^(?P<project>[0-9a-f-]+)$',
           view=views.ProjectDetailView.as_view(),
           name='detail',
       ),
       # RoleAssignment has a "project" member
       url(
           regex=r'^members/update/(?P<roleassignment>[0-9a-f-]+)$',
           view=views.RoleAssignmentUpdateView.as_view(),
           name='role_update',
       ),
   ]

Mixins
------

The ``projectroles.views`` module provides several useful mixins for augmenting
your views to add projectroles functionality.

**TODO: List**


Templates
=========

General Template Structure
--------------------------

**TODO**

Specific Views to be Implemented
--------------------------------

**TODO**

Rules
-----

**TODO**

Template Tags
-------------

**TODO**


Rules
=====

Create a file ``rules.py`` in your app directory. You should declare at least
one basic rule for enabling a user to view the app data for the project. This
can be named e.g. ``{APP_NAME}.view_data``. Predicates for the rules can be
found in projectroles and they can be extended within your app if needed.

.. code-block::
   import rules
   from projectroles import rules as pr_rules

   rules.add_perm(
       'example_project_app.view_data',
       rules.is_superuser | pr_rules.is_project_owner |
       pr_rules.is_project_delegate | pr_rules.is_project_contributor |
       pr_rules.is_project_guest)


ProjectAppPlugin
================

Create a file ``plugins.py`` in your app directory. In the file, declare
a ``ProjectAppPlugin`` class implementing
``projectroles.plugins.ProjectAppPluginPoint``. Within the class, implement
member variables and functions as instructed in comments and docstrings.

.. code-block::
   from projectroles.plugins import ProjectAppPluginPoint
   from .urls import urlpatterns

   class ProjectAppPlugin(ProjectAppPluginPoint):
       """Plugin for registering app with Projectroles"""
       name = 'example_project_app'
       title = 'Example Project App'
       urls = urlpatterns
       # ..

The following variables and functions are **mandatory**:

- ``name``: App name (ideally should correspond to the app package name)
- ``title``: Printable app title
- ``urls``: Urlpatterns (usually from the app's ``urls.py`` file)
- ``icon``: Font Awesome 4.7 icon name (without the ``fa-*`` prefix)
- ``entry_point_url_id``: Template path for the app entry point (**NOTE:** Must
  take the project ``omics_uuid`` as a kwarg named ``project``)
- ``description``: Verbose description of app
- ``app_permission``: Basic permission for viewing app data in project (see
  above)
- ``search_enable``: Boolean for enabling/disabling app search
- ``details_template``: Path to template to be included in the project details
  page, usually called ``{APP_NAME}/_details_card.html``
- ``details_title``: Title string to be displayed in the project details page
  for the app details template
- ``plugin_ordering``: Number to define the ordering of the app on the project
  menu sidebar and the details page


Implementing the following is **optional**:

- ``project_settings``: Implement if project-specific settings for the app are
  needed
- ``search_types``: Implement if searching the data of the app is enabled
- ``search_template``: Implement if searching the data of the app is enabled
- ``get_taskflow_sync_data()``: Applicable only if working with
  ``sodar_taskflow`` and iRODS
- ``get_object_link()``: If Django models are associated with the app. Used e.g.
  by ``django-sodar-timeline``.
- ``search()``: Function called when searching for data related to the app if
  search is enabled

Once you have implemented the ``rules.py`` and ``plugins.py`` files and added
the app and its URL patterns to the Django site configuration, you can create
the project app plugin in the Django databse with the following command:

.. code-block::
   $ ./manage.py syncplugins

You should see the following output to ensure the plugin was successfully
registered:

.. code-block::
   Registering Plugin for {APP_NAME}.plugins.ProjectAppPlugin
