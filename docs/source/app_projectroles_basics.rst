.. _app_projectroles_basics:


Projectroles Basics
^^^^^^^^^^^^^^^^^^^

The basic concepts and functionalities of the ``projectroles`` app are detailed
in this document.


Projects
========

The projectroles app groups project-specific data, user access roles and other
features into **projects** and **categories**. These can be nested in a tree
structure with the *category* type working as a container for sub-projects with
no project content of its own.


User Roles in Projects
======================

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
    Django **superuser** status overrides project role access.

The projectroles app provides the following features for managing user roles in
projects:

- Adding/modifying/removing site users as project members
- Inviting people not yet using the site by email
- Importing members from other projects (**NOTE:** disabled pending update)
- Automated emailing of users regarding role changes
- **TODO:** Mirroring user roles to/from an external projectroles-enabled site
  (will be added in SODAR Core v0.3)

.. note::
    Currently, only superusers can assign owner roles for top-level categories.


Rule System
===========

Projectroles uses the `django-rules <https://github.com/dfunckt/django-rules>`_
package to manage permissions for accessing data, apps and functionalities
within projects based on the user role. Predicates for project roles are
provided by the projectroles app and can be used and extended for developing
rules for your other project-specific Django apps.


Plugins
=======

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
==============

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

**TODO**: Describe these in :ref:`app_projectroles_usage`.


Templates and Styles
====================

Projectoles provides views and templates for all GUI-related functionalities
described above. The templates utilize the plugin framework to provide content
under projects dynamically. The project also provides default CSS stylings, base
templates and a base layout which can be used or adapted as needed. See the
usage and app development documentation for more details.
