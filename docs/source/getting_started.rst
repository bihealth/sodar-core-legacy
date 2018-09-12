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

- **projectroles**: The required base app for project access management and
  dynamic app content management
- **userprofile**: User profile app (requires projectroles)

The following packages are included in the repository for development and
as examples:

- **config**: Example Django site configuration
- **docs**: Usage and development documentation
- **example_project_app**: Example SODAR Core compatible project app
- **example_site**: Example/development Django site
- **example_site_app**: Example SODAR Core compatible site-wide app
- **requirements**: Requirements for SODAR Core  and development
- **utility**: Setup scripts for development


The Projectroles App
====================

The ``projectroles`` app is the base app for building a SODAR Core based Django
site. It provides a framework for project access management, dynamic content
including with django-plugins, models and tools for SODAR-compatible apps plus a
default template and CSS layout.

Other Django apps which intend to use aforementioned functionalities depend on
projectroles. While the Django app configuration can be dynamic, having
projectroles installed is **mandatory** for working with the SODAR project and
app structure.

Projects
--------

The projectroles app groups project-specific data, user access roles and other
features into **projects** and **categories**. These can be nested in a tree
structure with the *category* type working as a container for sub-projects with
no project content of its own.

User Roles in Projects
----------------------

User access to projects is granted by per-project assigning of roles. In each
project, a user can have one role at a time. New types of roles can be defined
by extending the default model's database table.

The default setup of role types used in SODAR sites:

- **project owner**
    - Full read/write access to project data and roles
    - Can create sub-projects under owned projects
    - One per project
    - Must be specified upon project creation
- **project delegate**
    - Full read/write access to project data
    - Can modify roles except for owner and delegate
    - One per project (to be increased in a further update)
    - Assigned by owner
- **project contributor**
    - Can read and write project data
    - Can modify and delete own data
- **project guest**
    - Read only access to project data

.. note::
    A Django **superuser** status overrides project role access.

The projectroles app provides the following features for managing user roles in
projects:

- Adding/modifying/removing site users as project members
- Inviting people not yet using the site by email
- Importing members from other projects (**NOTE:** disabled pending update)
- Automated emailing of users regarding role changes
- **TODO:** Mirroring user roles to/from an external projectroles-enabled site
  (will be added in v0.3)

.. note::
    Currently, only superusers can assign owner roles for top-level categories.

Rule System
-----------

Projectroles uses the `django-rules <https://github.com/dfunckt/django-rules>`_
package to manage permissions for accessing data, apps and functionalities
within projects based on the user role. Predicates for project roles are
provided by the projectroles app and can be used and extended for developing
rules for your other project-specific Django apps.

Plugins
-------

Projectroles provides a plugin framework to enable integrating apps and
content dynamically to a projectroles-enabled Django site. Types of plugins
currently included:

- **Project apps**: Apps tied to specific projects, making use of project roles,
  rules and other projectroles functionalities.
- **Site apps**: Site-wide Django apps which are not project-specific
- **Backend apps**: Backend apps without GUI entry points or (usually) views,
  imported and used dynamically by other SODAR-based apps for e.g. connectivity
  to external resources.

Existing apps can be modified to conform to the plugin structure by implementing
certain variables, functions, views and templates within the app. For more
details, see the app development documents.

Other Features
--------------

Other features in the projectroles app:

- **Project settings**: Setting values for app and project specific variables,
  which can be defined in project plugins
- **Project starring**: Ability for users to star projects as their favourites
- **Project search**: Functionality for searching data within projects using
  functions implemented in project app plugins
- **Tour help**: Inline help for pages
- **Project readme**: README document for each project with Markdown support
- **Custom user model**: Additions to the standard Django user model
- **Multi-Domain LDAP/AD support**: Support for LDAP/AD users from multiple
  domains
- **SODAR Taskflow and SODAR Timeline integration**: Included but disabled
  unless backend apps for Taskflow and Timeline are integrated in the Django
  site

**TODO**: Describe these in :ref:`usage`.

Templates and Styles
--------------------

Projectoles provides views and templates for all GUI-related functionalities
described above. The templates utilize the plugin framework to provide content
under projects dynamically. The project also provides default CSS stylings, base
templates and a base layout which can be used or adapted as needed. See the
usage and app development documentation for more details.


The Userprofile App
===================

The ``userprofile`` app is a site app, which currently provides a user profile view
for Projectroles-compatible Django users. It will later be expanded to cover
user-specific settings for SODAR-based sites.


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
