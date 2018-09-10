Getting Started
^^^^^^^^^^^^^^^

Basic concepts of SODAR Projectroles usage and/or development are detailed in
this document.


Repository Contents
===================

The following packages are included in the ``sodar_projectroles`` repository:

- **config**: Example Django site configuration
- **docs**: Usage and development documentation
- **example_project_app**: Example projectroles-enabled Django project app
- **example_site**: Example/development Django site
- **example_site_app**: Example Projectroles-enabled general Django app
- **projectroles**: The projectroles app itself
- **requirements**: Requirements for the projectroles app and development
- **user_profile**: User profile app (installed with projectroles)
- **utility**: Setup scripts for development


Projectroles Basics
===================

Projectroles provides the following functionalities for a Django-based web site.

Projects
--------

The projectroles app groups project-specific data, user access roles and other
features into **projects** and **categories**. These can be nested in a tree
structure with the *category* type working as a container for sub-projects.

User Roles in Projects
----------------------

User access to projects is granted by per-project assigning of roles. In each
project, a user can have one role at a time. New types of roles can be defined
by extending the default model's database table.

The current setup of role types used in SODAR sites:

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

The projectroles app provides the following features for managing user roles in
projects:

- Adding/modifying/removing site users as project members
- Inviting people not yet using the site by email
- Importing members from other projects (**NOTE:** disabled pending update)
- Automated emailing of users regarding role changes
- **TODO:** Mirroring user roles to/from an external projectroles-enabled site

**NOTE:** Currently, only site admins can assign owner roles for top-level
projects.

Rule System
-----------

Projectroles uses rules to manage permissions for accessing data, apps and
functionalities within projects based on the user role. Predicates for project
roles are provided by the projectroles app and can be used and extended for
developing rules for your other project-specific Django apps.

Plugins
-------

Projectroles provides a plugin framework to enable integrating apps and
content dynamically to a projectroles-enabled Django site. Types of plugins
currently included:

- **Project apps**: Apps tied to specific projects, making use of project roles,
  rules and other projectroles functionalities.
- **Site apps**: Non-project-specific Django apps
- **Backend apps**: Backend Django apps imported and used dynamically by
  projectroles-enabled apps for e.g. connectivity to external resources or
  accessing other Django apps' backend features.

Existing apps can be modified to conform to the plugin structure by implementing
certain variables, functions, views and templates within the app. For more
details, see the development section.

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

Templates and Styles
--------------------

Projectoles provides views and templates for all GUI-related functionalities
described above. The templates utilize the plugin framework to provide content
under projects dynamically. The project also provides default CSS stylings, base
templates and a base layout which can be used or adapted as needed. See the
usage and development documentation for more details.


Requirements
============

Major requirements for integrating the projectroles app into your Django site
and/or participating in development are listed below. For a complete requirement
list, see the ``requirements`` and ``utility`` directories in the repository.
Listed with minimum versions supported.

- Python 3.5
- Django 1.11.x (**NOTE:** 2.x not currently supported)
- PostgreSQL 9.4 and psycopg2
- Bootstrap 4.1.1
- JQuery 3.2.1
- Shepherd 1.8.1 with Tether 1.4.4
- Clipboard.js 2.0.0
- DataTables 1.10.18 with JQuery UI, FixedColumns, FixedHeader, Buttons, KeyTables
