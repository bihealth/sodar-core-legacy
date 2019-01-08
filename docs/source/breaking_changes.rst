.. _breaking_changes:

Breaking Changes
^^^^^^^^^^^^^^^^

This document details breaking changes from previous SODAR Core releases. It is
recommended to review these notes whenever upgrading from an older SODAR Core
version. For a complete list of changes in the current release, see the
``CHANGELOG.rst`` file.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


v0.4.1
======

System Prerequisites
--------------------

Changes in system requirements:

- **Python 3.6 or newer required**: 3.5 and older releases no longer supported.
- **PostgreSQL 9.6** is the recommended minimum version for the database.

Site Messages in Login Template
-------------------------------

If your site overrides the default login template in
``projectroles/login.html``, make sure your overridden version contains an
include for ``projectroles/_messages.html``. Following the SODAR Core template
conventions, it should be placed as the first element under the
``container-fluid`` div in the ``content`` block. Otherwise, site app messages
not requiring user authorization will not be visible on the login page. Example:

.. code-block:: django

  {% block content %}
    <div class="container-fluid">
      {# Django messages / site app messages #}
      {% include 'projectroles/_messages.html' %}
      {# ... #}
    </div>
  {% endblock content %}


v0.4.0
======

List Button Classes in Templates
--------------------------------

Custom small button and dropdown classes for including buttons within tables and
lists have been modified. The naming has also been unified. The following
classes should now be used:

- Button group: ``sodar-list-btn-group`` (formerly ``sodar-edit-button-group``)
- Button: ``sodar-list-btn``
- Dropdown: ``sodar-list-dropdown`` (formerly ``sodar-edit-dropdown``)

See projectroles templates for examples.

.. warning::

    The standard bootstrap class ``btn-sm`` should **not** be used with these
    custom classes!

SODAR Taskflow v0.3.1 Required
------------------------------

If using SODAR Taskflow, this release requires release v0.3.1 or higher due to
mandatory support of the ``TASKFLOW_SODAR_SECRET`` setting.

Taskflow Secret String
----------------------

If you are using the ``taskflow`` backend app, you **must** set the value of
``TASKFLOW_SODAR_SECRET`` in your Django settings. Note that this must match the
similarly named setting in your SODAR Taskflow instance!


v0.3.0
======

Remote Site Setup
-----------------

For specifying the role of your site in remote project metadata synchronization,
you will need to add two new settings to your Django site configuration:

The ``PROJECTROLES_SITE_MODE`` setting sets the role of your site in remote
project sync and it is **mandatory**. Accepted values are ``SOURCE`` and
``TARGET``. For deployment, it is recommended to fetch this setting from
environment variables.

If your site is set in ``TARGET`` mode, the boolean setting
``PROJECTROLES_TARGET_CREATE`` must also be included to control whether
creation of local projects is allowed. If your site is in ``SOURCE`` mode, this
setting can be included but will have no effect.

Furthermore, if your site is in ``TARGET`` mode you must include the
``PROJECTROLES_ADMIN_OWNER`` setting, which must point to an existing local
superuser account on your site.

Example for a ``SOURCE`` site:

.. code-block:: python

    # Projectroles app settings
    PROJECTROLES_SITE_MODE = env.str('PROJECTROLES_SITE_MODE', 'SOURCE')

Example for a ``TARGET`` site:

.. code-block:: python

    # Projectroles app settings
    PROJECTROLES_SITE_MODE = env.str('PROJECTROLES_SITE_MODE', 'TARGET')
    PROJECTROLES_TARGET_CREATE = env.bool('PROJECTROLES_TARGET_CREATE', True)
    PROJECTROLES_ADMIN_OWNER = env.str('PROJECTROLES_ADMIN_OWNER', 'admin')

General API Settings
--------------------

Add the following lines to your configuration to enable the general API
settings:

.. code-block:: python

    SODAR_API_DEFAULT_VERSION = '0.1'
    SODAR_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar+json'

DataTables Includes
-------------------

Includes for the DataTables Javascript library are no longer included in
templates by default. If you want to use DataTables, include the required CSS
and Javascript in relevant templates. See the ``projectroles/search.html``
template for an example.
