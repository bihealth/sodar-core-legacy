.. _project_app_dev:

Project App Development
^^^^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for developing
**project apps** to be used with the SODAR Core framework. This also applies for
modifying existing apps into project apps.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.

.. hint::

   The package ``example_project_app`` in the projectroles repository provides
   a concrete minimal example of a working project app.


Project App Basics
==================

**Characteristics** of a project app:

- Provides a functionality related to a project
- Is dynamically included in project views by projectroles using plugins
- Uses the project-based role and access control provided by projectroles
- Is included in projectroles search (optionally)
- Provides a dynamically included element (e.g. content overview) for the
  project details page
- Appears in the project menu sidebar in the default projectroles templates

**Requirements** for setting up a project app:

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
(see :ref:`integration`). The instructions can be applied either to modify a
previously existing app, or to set up a fresh app generated in the standard way
with ``./manage.py startapp``.

It is also assumed that apps are more or less created according to best
practices defined by `Two Scoops <https://www.twoscoopspress.com/>`_, with the
use of `Class-Based Views <https://docs.djangoproject.com/en/1.11/topics/class-based-views/>`_
being a requirement.


Models
======

In order to hook up your Django models into projects, there are two
requirements: implementing a **project foreign key** and a **UUID field**.

Project Foreign Key
-------------------

Add a ``ForeignKey`` field for the ``projectroles.models.Project`` model,
either called ``project`` or accessible with a ``get_project()`` function
implemented in your model.

.. note::

    If your app contains a complex model structure with e.g. nested models using
    foreign keys, it's not necessary to add this to all your models, just the
    topmost one(s) used e.g. in URL kwargs.

Model UUID Field
----------------

To provide a unique identifier for objects in the SODAR context, add a
``UUIDField`` with the name of ``omics_uuid`` into your model.

.. note::

    Projectroles links to objects in URLs, links and forms using UUIDs instead
    of database private keys. This is strongly recommended for all Django models
    in apps using the projectroles framework.

.. note::

    When updating an existing Django model with an existing database, the
    ``omics_uuid`` field needs to be populated. See
    `instructions in Django documentation <https://docs.djangoproject.com/en/1.11/howto/writing-migrations/#migrations-that-add-unique-fields>`_
    on how to create the required migrations.

Model Example
-------------

Below is an example of a projectroles-compatible Django model:

.. code-block:: python

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


Rules File
==========

Create a file ``rules.py`` in your app's directory. You should declare at least
one basic rule for enabling a user to view the app data for the project. This
can be named e.g. ``{APP_NAME}.view_data``. Predicates for the rules can be
found in projectroles and they can be extended within your app if needed.

.. code-block:: python

    import rules
    from projectroles import rules as pr_rules

    rules.add_perm(
        'example_project_app.view_data',
        rules.is_superuser | pr_rules.is_project_owner |
        pr_rules.is_project_delegate | pr_rules.is_project_contributor |
        pr_rules.is_project_guest)


ProjectAppPlugin
================

Create a file ``plugins.py`` in your app's directory. In the file, declare a
``ProjectAppPlugin`` class implementing
``projectroles.plugins.ProjectAppPluginPoint``. Within the class, implement
member variables and functions as instructed in comments and docstrings.

.. code-block:: python

    from projectroles.plugins import ProjectAppPluginPoint
    from .urls import urlpatterns

    class ProjectAppPlugin(ProjectAppPluginPoint):
        """Plugin for registering app with Projectroles"""
        name = 'example_project_app'
        title = 'Example Project App'
        urls = urlpatterns
        # ...

The following variables and functions are **mandatory**:

- ``name``: App name (ideally should correspond to the app package name)
- ``title``: Printable app title
- ``urls``: Urlpatterns (usually imported from the app's ``urls.py`` file)
- ``icon``: Font Awesome 4.7 icon name (without the ``fa-*`` prefix)
- ``entry_point_url_id``: View ID for the app entry point (**NOTE:** The view
  **must** take the project ``omics_uuid`` as a kwarg named ``project``)
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

.. code-block:: console

    $ ./manage.py syncplugins

You should see the following output to ensure the plugin was successfully
registered:

.. code-block:: console

    Registering Plugin for {APP_NAME}.plugins.ProjectAppPlugin

For info on how to implement the specific required views/templates, see the end
of this document.


Views
=====

Certain guidelines must be followed in developing views for them to be
successfully used by projectroles.

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
- Same as above, but the Django model provides a
  ``get_project()`` function which returns (you guessed it) a
  ``Projectroles.models.Project`` object.

Examples:

.. code-block:: python

   urlpatterns = [
       # Direct reference to the Project model
       url(
           regex=r'^(?P<project>[0-9a-f-]+)$',
           view=views.ProjectDetailView.as_view(),
           name='detail',
       ),
       # RoleAssignment model has a "project" member which is also OK
       url(
           regex=r'^members/update/(?P<roleassignment>[0-9a-f-]+)$',
           view=views.RoleAssignmentUpdateView.as_view(),
           name='role_update',
       ),
   ]

Mixins
------

The ``projectroles.views`` module provides several useful mixins for augmenting
your view classes to add projectroles functionality. These can be found in the
``projectroles.views`` module.

The most commonly used mixins:

- ``LoggedInPermissionMixin``: Ensure correct redirection of users on no
  permissions
- ``ProjectPermissionMixin``: Provides a ``Project`` object for permission
  checking based on URL kwargs
- ``ProjectContextMixin``: Provides a ``Project`` object into the view context
  based on URL kwargs

See ``example_project_app.views.ExampleView`` for an example.

**TODO:** Provide a proper auto-generated docstring reference?


Templates
=========

Template Structure
------------------

It is strongly recommended to extend ``projectroles/project_base.html`` in your
project app templates. Just start your template with the following line:

.. code-block:: django

   {% extends 'projectroles/project_base.html' %}

The following **template blocks** are available for overriding or extending:

- ``title``: Page title
- ``css``: Custom CSS (extend with ``{{ block.super }}``)
- ``projectroles_extend``: Your app content goes here!
- ``javascript``: Custom Javascript (extend with ``{{ block.super }}``)
- ``head_extend``: Optional block if you need something extra inside the HTML ``<head>`` element

Recommended CSS classes for wrapping your page title and actual content:

.. code-block:: html

   <div class="row sodar-subtitle-container">
     <h3><i class="fa fa-{ICON}"></i> App/Functionality Title</h3>
   </div>

   <div class="container-fluid sodar-page-container">
     <p>Content goes here!</p>
   </div>

See ``example_project_app/example.html`` for a minimal commented template example.

.. hint::

   If you include some controls on your ``sodar-subtitle-container`` class and
   want it to remain sticky on top of the page while scrolling, add the
   ``bg-white sticky-top`` classes to the element.

Rules
-----

To control user access within a template, just do it as follows:

.. code-block:: django

   {% load rules %}
   {% has_perm 'app.do_something' request.user project as can_do_something %}

This checks if the current user from the HTTP request has permission for
``app.do_something`` in the current project retrieved from the page context.

Template Tags
-------------

General purpose template tags are available in
``projectroles/templatetags/projectroles_common_tags.py``. Include them to your
template as follows:

.. code-block:: django

   {% load projectroles_common_tags %}


Specific Views and Templates
============================

A few specific views/templates are expected to be implemented.

App Entry Point
----------------

As described in the Plugins chapter, an app entry point view is to be defined
in the ``ProjectAppPlugin``. This is **mandatory**.

The view **must** take a ``project`` URL kwarg which corresponds to a
``Project.omics_uuid``.

For an example, see ``example_project_app.views.ExampleView`` and the associated
template.

Project Details Element
-----------------------

A sub-template to be included in the project details page (the project's "front
page" provided by projectroles, where e.g. overview of app content is shown).

Traditionally these files are called ``_details_card.html``, but you can name
them as you wish and point to the related template in the ``details_template``
variable of your plugin.

It is expected to have the content in a ``card-body`` container:

.. code-block:: django

   <div class="card-body">
     {# Content goes here #}
   </div>

Project Search Function and Template
====================================

If you want to implement search in your project app, you need to implement the
``search()`` function in your plugin as well as a template for displaying the
results.

.. hint::

   Implementing search *can* be complex. If you have access to the main SODAR
   repository, apps in that project might prove useful examples.

The search() Function
---------------------

See the signature of ``search()`` in
``projectroles.plugins.ProjectAppPluginPoint``. The arguments are as follows:

- ``search_term``
    - Term to be searched for (string). Should be self-explanatory.
    - Multiple strings or separating multiple phrases with quotation marks not
      yet supported.
- ``user``
    - User object for user initiating search
- ``search_type``
    - The type of object to search for (string, optional)
    - Used to restrict search to specific types of objects
    - You can specify supported types in the plugin's ``search_types`` list.
    - Examples: ``file``, ``sample``..
- ``keywords``
    - Special search keywords, e.g. "exact"
    - **NOTE:** Currently not implemented

.. note::

   Within this function, you are expected to verify appropriate access of the
   seaching user yourself!

The return data is a dictionary, which is split by groups in case your app can
return multiple different lists for data. This is useful where e.g. the same
type of HTML list isn't suitable for all returnable types. If only returning one
type of data, you can just use e.g. ``all`` as your only category. Example of
the result:

.. code-block:: python

   return {
       'all': {                     # 1-N categories to be included
           'title': 'List title',   # Title of the result list to be displayed
           'search_types': [],      # Object types included in this category
           'items': []              # The actual objects returned
           }
       }

**TODO:** Example of an implemented function

Search Template
----------------

Projectroles will provide your template context the ``search_results`` object,
which corresponds to the result dict of the aforementioned function. There are
also includes for formatting the results list, which you are encouraged to use.

Example of a simple results template, in case of a single ``all`` category:

.. code-block:: django

   {% if search_results.all.items|length > 0 %}

     {# Include standard search list header here #}
     {% include 'projectroles/_search_header.html' with search_title=search_results.all.title result_count=search_results.all.items|length %}

     {# Set up a table with your results #}
     <table class="table table-striped omics-card-table omics-search-table" id="omics-ff-search-table">
       <thead>
         <tr>
           <th>Name</th>
           <th>Some Other Field</th>
         </tr>
      </thead>
      <tbody>
        {% for item in search_results.all.items %}
          <tr>
            <td>
              <a href="#link_to_somewhere_in your_app">{{ item.name }}</a>
            </td>
            <td>
              {{ item.some_other_field }}
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {# Include standard search list footer here #}
    {% include 'projectroles/_search_footer.html' %}

  {% endif %}


TODO
====

- Naming conventions
- Template design guidelines
- Examples of common things (e.g. forms)
