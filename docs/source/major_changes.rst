.. _major_changes:


Major Changes
^^^^^^^^^^^^^

This document details highlighted updates and breaking changes in SODAR Core
releases. It is recommended to review these notes whenever upgrading from an
older SODAR Core version. For a complete list of changes in current and previous
releases, see the :ref:`full changelog<changelog>`.


v0.10.11 (2022-03-22)
*********************

Release Highlights
==================

- Add sidebar icon resizing
- Change project create form to require manual setting of project type
- Fix project visibility in project list for inherited owners
- General bug fixes and minor updates

Breaking Changes
================

Search Result Context Data in Tests
-----------------------------------

In context data for ``ProjectSearchResultsView``, the ``app_search_data``
dictionary has been renamed into ``app_results``. This does not affect
implementing the search functionality from your apps, but if you test that
functionality by asserting search view output, you have to rename this dict in
your test cases.


v0.10.10 (2022-03-03)
*********************

Release Highlights
==================

- Fix layout issues
- Fix search issues
- General bug fixes and minor updates

Breaking Changes
================

N/A


v0.10.9 (2022-02-16)
********************

Release Highlights
==================

- Add anonymous access support for Ajax API views
- Update project list for client side loading
- Update timeline app status change retrieval and rendering
- Optimize project list queries
- General bug fixes and minor updates

Breaking Changes
================

N/A


v0.10.8 (2022-02-02)
********************

Release Highlights
==================

- Drop Python 3.7 support, add Python 3.10 support
- Display missing site settings in siteinfo app
- Fix project creation owner assignment for non-owner category members
- Improve layout in siteinfo and timeline apps
- Upgrade third party Python package dependencies
- Optimize queries in timeline app

Breaking Changes
================

System Prerequisites
--------------------

SODAR Core no longer supports Python 3.7. Python 3.8 is currently both the
minimum and default version to run SODAR Core and its dependencies.

Third party Python package dependencies have been upgraded. See the
``requirements`` directory for up-to-date package versions and upgrade your
project accordingly.

Deprecated Selenium Methods
---------------------------

The minimum Selenium version has been upgraded to v4.0.x. Some test methods have
been deprecated in this version and will be removed in a future releases. UI
test helpers from this version onwards will use the non-deprecated versions. You
should the dependency in your projects, run tests, check the output and update
any deprecated method calls if used.

Timeline App API Updated
------------------------

If you are using ``TimelineAPI.get_event_description()`` in your own apps,
please note that the method signature has changed. This may affect the use of
positional arguments.


v0.10.7 (2021-12-14)
********************

Release Highlights
==================

- Search bug fixes
- REST API project type restriction fixes
- General bug fixes and minor updates
- Upgraded dependencies

Breaking Changes
================

System Prerequisites
--------------------

The following minimum versions have been bumped:

- ``django>=3.2.10, <3.3``
- ``python-ldap==3.4.0``

API View Invalid Project Type Response
--------------------------------------

If ``project_type`` is set in a REST API view and that view is called with an
disallowed value, the view will return HTTP 403 instead of 400. The cause for
this response is included in the ``detail`` field.


v0.10.6 (2021-11-19)
********************

Release Highlights
==================

- Add additional emails for users
- Add project type restriction for API views
- Add profiling middleware
- Improve management command output
- Improve user representation in email
- Optimize project list queries
- Timeline app bug fixes
- Search results layout fixes
- General bug fixes and minor updates
- Upgraded dependencies

Breaking Changes
================

System Prerequisites
--------------------

The minimum Django version has been bumped to v3.2.9.

Search Results DataTables Upgrade
---------------------------------

DataTables includes on the search results page have been upgraded to version
``bs4/dt-1.11.3/b-2.0.1``. You are advised to review the search results layout
for your own apps to ensure everything looks correct.

Project.has_public_children() Removed
-------------------------------------

The ``Project`` model ``has_public_children()`` helper has been removed. In its
place, you should use the ``Project.has_public_children`` field.


v0.10.5 (2021-09-20)
********************

Release Highlights
==================

- Display project badge in app alerts
- Custom email header and footer
- Fix remote sync of non-projectroles app settings
- Multiple app settings remote sync bug fixes
- General bug fixes and minor updates
- Upgraded dependencies

Breaking Changes
================

System Prerequisites
--------------------

The minimum Django version has been bumped to v3.2.7.

Template Tag Removed
--------------------

The ``get_plugin_name_by_id()`` template tag has been removed from
``projectroles_common_tags``. There should be no reason to query app plugins by
database ID. Please use e.g. the utilities found in ``projectroles.plugins``
instead.


v0.10.4 (2021-08-19)
********************

Release Highlights
==================

- Appalerts list view UI improvements
- Siteinfo app and UI improvements
- Fix API and UI views to return 404 status code if object is not found
- General bug fixes and minor updates
- Upgraded dependencies

Breaking Changes
================

System Prerequisites
--------------------

The minimum Django version has been bumped to v3.2.6.

Base UI and API View 404 Responses
----------------------------------

Base UI and API views have been fixed to correctly return HTTP 404 to authorized
users for resources that are not found. This may affect some test cases which
still operate under the assumption of the views returning 403 instead.


v0.10.3 (2021-07-01)
********************

Release Highlights
==================

- General bug fixes and minor updates
- Upgraded dependencies

Breaking Changes
================

System Prerequisites
--------------------

The minimum Django version has been bumped to v3.2.5.

The following third party Python package requirements have been upgraded:

- ``sphinx-rtd-theme>=0.5.2, <0.6`` (base)
- ``black==21.6b0`` (test)


v0.10.2 (2021-06-03)
********************

Release Highlights
==================

- Project list bug fixes
- General bug fixes and minor updates
- Upgraded dependencies
- Minor changes

Breaking Changes
================

System Prerequisites
--------------------

The minimum Django version has been bumped to v3.2.4.

Third party Python package requirements have been upgraded. See the
``requirements`` directory for up-to-date package versions.


v0.10.1 (2021-05-06)
********************

Release Highlights
==================

- Add JQuery status updating for app alerts
- Make project available in PyPI
- Critical bug fixes for remote sync
- Bug fixes and minor updates

Breaking Changes
================

System Prerequisites
--------------------

The minimum versions of dependencies have been bumped as follows:

- Django: v3.2.1
- Django-debug-toolbar: v3.2.1

Base Template Updated
---------------------

If you are overriding the ``base_site.html`` with your own template and intend
to use the ``appalerts`` app, please add the following snippet into the
``javascript`` block in ``{SITE}/templates/base.html``:

.. code-block:: django

    {% block javascript %}
      {# ... #}
      <!-- App alerts Javascript -->
      {% include 'projectroles/_appalerts_include.html' %}
    {% endblock javascript %}

Remote Sync Bug in v0.9
-----------------------

A bug in remote project sync was recently discovered in SODAR Core v0.9.x and
v0.10.0. The bug has been fixed in this release, but the complete fix requires
for both the ``SOURCE`` and ``TARGET`` sites to be upgraded to v0.10. If you
need to use a site based on SODAR Core v0.9 as a remote sync target, please
upgrade your site to
`this hotfix branch <https://github.com/bihealth/sodar-core/tree/0.9.1/fix-settings-sync>`_.
Note that it is recommended to upgrade all your sites to v0.10 as soon as
possible.


v0.10.0 (2021-04-28)
********************

Release Highlights
==================

- Project upgraded to Django v3.2
- Minimum Python version requirement upgraded to 3.7
- Site icons access via Iconify
- Material Design Icons used as default icon set
- Appalerts app for app-generated user alerts
- Site-wide timeline events
- Timeline events without user
- Allow public guest access to projects for authenticated and anonymous users
- Display Django settings in Site Info app

Breaking Changes
================

System Prerequisites
--------------------

Python version requirements have been upgraded as follows:

- The **minimum** Python version is 3.7
- The **recommended** Python version is 3.8
- CI tests are run on Python 3.7, 3.8 and 3.9
- Support for Python 3.6 has been dropped.

It is recommended to always use the most recent minor version of a Python
release.

Third party Python package requirements have been upgraded. See the
``requirements`` directory for up-to-date package versions.

**Ubuntu 20.04 Focal** is now the recommended OS version for development.

Django v3.2 Upgrade
-------------------

This release updates SODAR Core from Django v1.11 to v3.2. This is a breaking
change which causes many updates and also requires updating several
dependencies.

To upgrade, please update the Django requirement along with your site's other
Python requirements to match ones in ``requirements/*.txt``. See
`Django deprecation documentation <https://docs.djangoproject.com/en/dev/internals/deprecation/>`_
for details about what has been deprecated in Django and which changes are
mandatory.

Common known issues:

- Minimum version of PostgreSQL has been raised to v9.5.
- ``ForeignKey`` fields in models must explicitly declare an ``on_delete``
  argument.
- ``is_authenticated()`` and ``is_anonymous()`` in the user model no longer
  work: use ``is_authenticated`` and ``is_anonymous`` instead.
- Replace imports from ``django.core.urlresolvers`` with ``django.urls``.
- Replace ``django.contrib.postgres.fields.JSONField`` with
  ``django.db.models.JSONField``.
- Add ``DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'`` in
  ``config/settings/base.py`` to get rid of database migration warnings.
- Replace ``{% load staticfiles %}`` with ``{% load static %}``.

In the future, the goal is to keep SODAR Core at the latest stable major version
of Django, except for potential cases in which a critical third party package
has not yet been updated to support a new release.

New Context Processors Required
-------------------------------

The following new context processors are required if you intend to include any
site apps to your projects, or make use of site-wide app alerts, respectively.
To make use of these features, please add the following processors in
``base.py`` under ``TEMPLATES``:

.. code-block:: python

    TEMPLATES = [
        {
            'OPTIONS': {
                'context_processors': {
                    # ...
                    'projectroles.context_processors.site_app_processor',
                    'projectroles.context_processors.app_alerts_processor',
                }
            }
        }

REST API Updates
----------------

The following changes have been made to REST API views:

- ``public_guest_access`` parameter added to project API views.

Site Icons Updated
------------------

Instead of directly including Font Awesome, site icons are now accessed as SVG
using `Iconify <https://iconify.design/>`_. The default icon set has been
changed from Font Awesome to `Material Design Icons <https://materialdesignicons.com>`_.
It is however possible to use other icon sets supported by Iconify for your own
SODAR Core apps.

To make your icons work with SODAR Core v0.10+, you will need to take the
following steps.

First, make sure ``django-iconify`` is installed. Add
``dj_iconify.apps.DjIconifyConfig`` to your Django site settings under
``THIRD_PARTY_APPS`` and ``dj_iconify.urls`` to your site URLs in
``config/urls.py``. See SODAR Core or SODAR Django Site settings for an example.

You will also need to set ``ICONIFY_JSON_ROOT`` in the base Django settings.

.. code-block:: django

    ICONIFY_JSON_ROOT = os.path.join(STATIC_ROOT, 'iconify')

If you are overriding the ``base_site.html`` template, add the following lines
to your base template:

.. code-block:: django

    <script type="text/javascript" src="{% url 'config.js' %}"></script>
    <script type="text/javascript" src="{% static 'projectroles/js/iconify.min.js' %}"></script>

Next, you must download the `Iconify JSON collection files <https://github.com/iconify/collections-json/>`_
required for hosting the icons on your Django server. It is recommended to use
the ``geticons`` management command for this. By default, this downloads the
required ``collections.json`` file along with the ``mdi.json`` file for the MDI
icon collection.

.. code-block:: console

    $ ./manage.py geticons

If you wish to also use other collections than MDI, add them as a list using
the ``-c`` argument. The following example downloads the additional ``carbon``
and ``clarity`` icon sets.

.. code-block:: console

    $ ./manage.py geticons -c carbon clarity

Make sure you run ``collectstatic`` after retrieving the collections for
development.

Before committing your code, it is recommended to update your ``.gitignore``
file with the following lines:

.. code-block::

    */static/iconify/*.json
    */static/iconify/json/*.json

To make the icons in your apps work with this change, you must change the icon
syntax in your Django templates. Use ``iconify`` as the base class of the icon
element. Enter the collection and icon name into the ``data-icon`` attribute.

Example:

.. code-block:: HTML

    <i class="iconify" data-icon="mdi:home"></i>

Also make sure to modify the ``icon`` attribute of your app plugins to include
the full ``collection:name`` syntax for Iconify icons.

You may have to specify icon sizing manually in certain elements. In that
case, use the ``data-height`` and/or ``data-width`` attributes. For spinning
icons, add the ``spin`` class provided in ``projectroles.css``.

Once you have updated all your icons, you can remove the Font Awesome CSS
include from your base template if you are not directly importing it from
``base_site.html``.

In certain client side Javascript implementations in which icons are loaded or
replaced dynamically, you may have to refer to these URLs as a direct ``img``
element:

.. code-block:: HTML

    <img src="/icons/mdi/home.svg" />

For modifiers such as color and size when using ``img`` tags,
`see here <https://docs.iconify.design/implementations/css.html>`_.

Deprecated Features Removed
---------------------------

The following previously deprecated features have been removed in this release:

- ``Project.get_full_title()`` has been removed. Use ``Project.full_title``
  instead.
- Old style search with a single ``search_term`` argument has been removed. Make
  sure your search implementation expects and uses a ``search_terms`` list
  instead.

Timeline API Changes
--------------------

The signatures for ``get_object_url()`` and ``get_object_link()`` helpers have
changed. They now expect the object itself as first argument, followed by an
optional ``Project`` object. The same also applies for
``get_history_dropdown()`` in projectroles common template tags.

Public Guest Access Support
---------------------------

This version adds public guest access support for projects. By setting
``PROJECTROLES_ALLOW_ANONYMOUS`` true, this can be extended to anonymous users.
For your views to properly support anonymous access, please use the override of
``LoginRequiredMixin`` provided in ``projectroles.views`` instead of the
original mixin supplied in Django.

GitHub Repository Updates
-------------------------

The GitHub repository for the project has been renamed from ``sodar_core`` to
``sodar-core``. Otherwise the URL remains the same:
`<https://github.com/bihealth/sodar-core/>`_

GitHub should redirect from the old name indefinitely. However, just to be sure
it is recommend to update your site's dependencies.

Additionally, the former ``master`` branch has been renamed to ``main``.


v0.9.1 (2021-03-05)
*******************

Release Highlights
==================

- Add inline head include from environment variables in base template
- Duplicate object UUIDs in REST API view nested lists

Breaking Changes
================

Base Template Updated
---------------------

The base site template in ``projectroles/base_site.html`` has been updated. If
you have copied the template to your own site's base template to extend it,
please make sure to copy the latest changes to maintain full compatibility. See
diff between templates or search for lines containing ``inline_head_include``.

Duplicate UUIDs in Nested REST API Lists
----------------------------------------

Nested object lists in SODAR Core REST API views are grouped into dictionaries
using each object's ``sodar_uuid``. From this version onwards, the UUID fields
are duplicated within each object as well. While this isn't a breaking change in
itself, if you use ``SODARNestedListSerializer`` it may cause some of your test
cases to fail unless altered.


v0.9.0 (2021-02-03)
*******************

Release Highlights
==================

- Last major update based on Django v1.11
- Enable modifying local app settings in project update form on target sites
- Add projectroles app settings
- Add remote sync for global projectroles app settings
- Add IP address based access restriction for projects
- Add SSO support via SAML
- Add support for local user invites and local user account creation
- Add batch invites and role updates via management command
- Add REST API views for project invite management
- Add advanced search with multiple terms
- Add REST API view for current user info retrieval

Breaking Changes
================

Development Helper Scripts
--------------------------

Development helper scripts (``.sh``) have been replaced by a ``Makefile``.
Get an overview of the available commands via ``make usage``.

System Prerequisites
--------------------

Third party Python package requirements have been upgraded. See the
``requirements`` directory for up-to-date package versions.

The following third party JS/CSS requirements have been updated:

- JQuery v3.5.1
- Bootstrap v4.5.3

.. note::

    This is the last major update of SODAR Core based on and supporting Django
    v1.11, which is now out of long term support. From v0.10 onwards, SODAR Core
    based sites must be implemented on Django v3.x+.

ProjectAppPlugin Search Updates
-------------------------------

The expected signature for ``ProjectAppPluginPoint.search()`` has changed.
Instead of the ``search_term`` string argument, ``search_terms`` is expected.
This argument is a list of strings expected to be combined with ``OR``
operators.

See the ``filesfolders`` app for an example of the new implementation.

In SODAR Core v0.9, the old deprecated implementation still works, but searching
for multiple terms in the "Advanced Search" view will only return results for
the first search term given. This deprecation protection will be removed in the
next major version. Please update the ``search()`` methods in your project app
plugins if you have implemented them.

Project Full Title Field
------------------------

The full title of a project, including the entire category path, can now be
accessed via the ``Project.full_title``. This enables you to use the field
directly in your Django queries and ordering. The value of the field is
auto-populated on ``Project.save()`` and in a database migration accompanied in
this release.

As a result, the ``Project.get_full_title()`` has been deprecated and will be
removed in the next major SODAR Core release. Please refactor your usage of that
helper into referring to ``Project.full_title`` directly.


v0.8.4 (2020-11-12)
*******************

Release Highlights
==================

This release updates documentation for JOSS submission.

Breaking Changes
================

N/A


v0.8.3 (2020-09-28)
*******************

Release Highlights
==================

- Fix issues in remote project synchronization
- Fix crashes in ``siteinfo`` app from exceptions raised by plugins

Breaking Changes
================

Remote Project Sync and Local Categories
----------------------------------------

When working on a ``TARGET`` site, creating local projects under categories
synchronized from a ``SOURCE`` site is no longer allowed. This is done to avoid
synchronization clashes. If you want to enable local projects on your site in
addition to remote ones, you will need to create a local root category for them.

API Changes
-----------

``ProjectCreateAPIView`` now returns status ``403`` if called on a target site
with disabled local projects, instead of ``400`` as before.


v0.8.2 (2020-07-22)
*******************

Release Highlights
==================

- Enable site-wide background jobs
- Critical bug fixes for project member management
- Minor fixes and updates

Breaking Changes
================

N/A


v0.8.1 (2020-04-24)
*******************

Release Highlights
==================

- Fix checking for remote project status in projectroles REST API views
- Miscellaneous bug fixes

Breaking Changes
================

SODARAPIObjectInProjectPermissions Removed
------------------------------------------

The deprecated ``SODARAPIObjectInProjectPermissions`` base class has been
removed from ``projectroles.views_api``. Please base your REST API views to one
of the remaining base classes instead.


v0.8.0 (2020-04-08)
*******************

Release Highlights
==================

- Add API views for the ``projectroles`` and ``filesfolders`` apps
- Add new base view classes and mixins for API/Ajax views
- Import the ``tokens`` API token management app from VarFish
- Allow assigning roles other than owner for categories
- Allow category delegates and owners to create sub-categories and projects
- Allow moving categories and projects under different categories
- Inherit owner permissions from parent categories
- Allow displaying project apps in categories with ``category_enable``
- Reorganization of views in apps

Breaking Changes
================

Owner Permissions Inherited from Categories
-------------------------------------------

Starting in this version of SODAR Core, category owner permissions are
automatically inherited by projects below those categories, as well as possible
subcategories. If this does not fit your use case, it is recommend to reorganize
your project structure and/or give category access to admin users who have
access to all projects anyway.

Projectroles Views Reorganized
------------------------------

Views, base views related mixins for the ``projectroles`` app have been
reorganized in this version. Please review your projectroles imports.

The revised structure is as follows:

- UI views and related mixins **remain** in ``projectroles.views``
- Ajax API view classes were **moved** into ``projectroles.views_ajax``
- REST API view classes **moved** into ``projectroles.views_api``
- Taskflow API view classes **moved** into ``projectroles.views_taskflow``

The same applies to classes and mxins in view tests. See
``projectroles.tests.test_views*`` to update imports in your tests.

Renamed Projectroles View Classes
---------------------------------

In addition to reorganizing classes into different views, certain view classes
intended to be usable by other apps have been renamed. They are listed below.

- ``UserAutocompleteAPIView`` -> ``UserAutocompleteAjaxView``
- ``UserAutocompleteRedirectAPIView`` -> ``UserAutocompleteRedirectAjaxView``

API View Class Changes
----------------------

``SODARAPIBaseView`` and ``APIPermissionMixin`` have been removed. Please use
appropriate classes and mixins found in ``projectroles.views_api`` and
``projectroles.views_ajax`` instead.

Base Test Class and Mixin Changes
---------------------------------

Base test classes and helper mixins in ``projectroles`` have been changed as
detailed below.

- ``SODARAPIViewMixin`` has been moved into ``projectroles.test_views_api`` and
  renamed into ``SODARAPIViewTestMixin``.
- ``KnoxAuthMixin`` has been combined into ``SODARAPIViewTestMixin``.
- ``get_accept_header()`` returns the header as dict instead of a string.
- ``assert_render200_ok()`` and ``assert_redirect()`` have been removed from
  ``TestPermissionBase``. Please use ``assert_response()`` instead.

In addition to the aforementioned changes, certain minor setup details such as
default user rights and may have changed. If you experience unexpected failures
in your tests, please review the SODAR Core base test classes and helper
methods, refactoring your tests where required.

User Group Updating
-------------------

The ``set_user_group()`` helper has been moved from ``projectroles.utils`` into
the ``SODARUser`` model. It is called automatically on ``SODARUser.save()``, so
manual calling of the method is not required for most cases.

System Prerequisites
--------------------

The following third party JS/CSS requirements have been updated:

- JQuery v3.4.1
- Bootstrap v4.4.1
- Popper.js v1.16.0

The minimum supported versions have been upgraded for a number of Python
packages in this release. It is highly recommended to also upgrade these for
your SODAR Core based site. See the ``requirements`` directory for up-to date
dependencies.

The minimum version requirement for Django has been bumped to 1.11.29.

Default Templates Modified
--------------------------

The default template ``base_site.html`` has been modified in this version. If
you override it with your own altered version, please review the difference and
update your templates as appropriate.

SODAR Taskflow v0.4.0 Required
------------------------------

If using SODAR Taskflow, this release requires release v0.4.0 or higher due to
required support for the ``role_update_irods_batch`` flow.

Known Issues
============

- Category roles beyond owner are not synchronized to target sites in remote
  project sync. This was omitted to maintain compatibility in existing APIs in
  this release. The feature is intended to be implemented in SODAR Core v0.9.
- Project/user app settings cannot be set or updated in the project REST API. A
  separate API for this will be developed. Currently the only way to modify
  app settings is via the GUI.


v0.7.2 (2020-01-31)
*******************

Release Highlights
==================

- Enforce API versions in remote project sync
- Separate base API views for SODAR Core API and external SODAR site APIs
- Redesign user autocomplete field
- Set issuing user email to ``reply-to`` header for role and invite emails
- Display hidden project app settings to superusers in project update form
- Allow providing custom keyword arguments for backend plugin ``get_api()``
  through ``get_backend_api()``
- Enable sorting custom project list columns in plugin definition
- Bug fixes for project list columns

Breaking Changes
================

User Autocomplete Field Redesigned
----------------------------------

User autocomplete field for forms with its related widget(s) have been
redesigned with breaking API changes. Please review the :ref:`dev_project_app`
documentation and modify your implementation accordingly.

Remote Project Sync API Version Enforcing
-----------------------------------------

The remote project sync view initiated from a ``TARGET`` site now sends the
version number, making the ``SOURCE`` site enforce allowed API versions in its
request. Hence, when a major breaking change is made on the source site and
version requirements updated, requests from the target site will no longer work
without upgrading to the latest SODAR Core version.

Exceptions Raised by get_backend_api()
--------------------------------------

The ``get_backend_api()`` method for retrieving backend plugin API objects
no longer suppresses potential exceptions raised by API object initialization.
If it is possible for your API object to raise an exception on initialization,
you will need to handle it when calling this method.

System Prerequisites
--------------------

The minimum version requirement for Django has been bumped to 1.11.27.

KnoxAuthMixin in Tests
----------------------

Default API configuration for methods in ``KnoxAuthMixin`` are now set to
internal SODAR Core API values. If you use the mixin in the tests of your site,
please update the arguments in your method calls accordingly. You can also now
supply the `media_type` argument for relevant functions. The
``get_accept_header()`` method has been moved to a separate
``SODARAPIViewMixin`` helper mixin.


v0.7.1 (2019-12-18)
*******************

Release Highlights
==================

- Project list layout and extra column handling improved
- Allow customizing widgets in app settings
- Enable managing global JS/CSS includes in Django settings
- Initial support for deploying site in kiosk mode
- Critical bug fixes for category and project owner management

Breaking Changes
================

Default Templates Modified
--------------------------

The default templates ``base_site.html`` and ``login.html`` have been modified
in this version. If you override them with your own altered versions, please
review the difference and update your templates as appropriate.

User Added to get_project_list_value()
--------------------------------------

The signature of the ``get_project_list_value()`` method implemented by project
app plugins to return data for extra project list columns has changed. The
``user`` argument which provides the current user has been added. If using this
feature, please make sure to update your implementation(s) of the method.

See :ref:`app_projectroles_api_django` to review the API changes.


v0.7.0 (2019-10-09)
*******************

Release Highlights
==================

- Sync peer project information for remote target sites
- Enable revoking access to remote projects
- Allow defining app settings in site apps
- "User in project" scope added into app settings
- Support JSON in app settings
- Project owner management moved to project member views

Breaking Changes
================

System Prerequisites
--------------------

The minimum supported versions have been upgraded for a number of Python
packages in this release. It is highly recommended to also upgrade these for
your SODAR Core based site. See the ``requirements`` directory for up-to date
dependencies.

Backend Javascript Include
--------------------------

The code in ``base.html`` which was including javascript from backend apps to
all templates in projectsroles was removed. Instead, Javascript and CSS
associated to a backend plugin should now be included in app templates as
needed. This is done using the newly introduced ``get_backend_include()``
template tag in ``projectroles_common_tags``.

Deprecated get_setting() Tag Removed
------------------------------------

The deprecated ``get_setting()`` template tag has been removed from
``projectroles_common_tags``. Please use ``get_django_setting()`` in your
templates instead.

ProjectSettingMixin Removed
---------------------------

In ``projectroles.tests.test_views``, the deprecated ``ProjectSettingMixin``
was removed. If you need to populate app settings in your tests, use the
``AppSettingAPI`` instead.

AppSettingAPI get_setting_defs() Signature Changed
--------------------------------------------------

The ``get_settings_defs()`` function in the app settings API now accepts either
a project app plugin or simply the name of the plugin as string. Due to this
change, the signature of the API function including argument order has changed.
Please see the :ref:`API documentation<app_projectroles_api_django>` for more
details and update your function calls accordingly.

Default Footer Styling Changed
------------------------------

The styling of the page footer and the default ``_footer.html`` have changed.
You no longer need an extra ``<div>`` element for the footer content, unless
you need to do styling overrides yourself.


v0.6.2 (2019-06-21)
*******************

Release Highlights
==================

- Allow hiding app settings from UI forms
- Add template tag for retrieving app settings

Breaking Changes
================

System Prerequisites
--------------------

The minimum version requirement for Django has been bumped to 1.11.21.

Template Tag for Django Settings Access Renamed
-----------------------------------------------

The ``get_setting()`` template tag in ``projectroles_common_tags`` has been
renamed into ``get_django_setting()``. In this version the old tag still works,
but this deprecation protection will be removed in the next release. Please
update any references to this tag in your templates.


v0.6.1 (2019-06-05)
*******************

Release Highlights
==================

- Add custom project list columns definable in ProjectAppPlugin
- Add example project list column implementation in the filesfolders app

Breaking Changes
================

App Settings Deprecation Protection Removed
-------------------------------------------

The deprecation protection set up in the previous release has been removed.
Project app plugins are now expected to declare ``app_settings`` in the format
introduced in v0.6.0.


v0.6.0 (2019-05-10)
*******************

Release Highlights
==================

- Add user specific settings
- Refactor project settings into project/user specific app settings
- Add siteinfo app

Breaking Changes
================

App Settings (Formerly Project Settings)
----------------------------------------

The former Project Settings module has been completely overhauled in this
version and requries changes to your app plugins.

The ``projectroles.project_settings`` module has been renamed into
``projectroles.app_settings``. Please update your dependencies accordingly.

Settings must now be defined in ``app_settings``. The format is identical to
the previous ``project_settings`` dictionary, except that a ``scope`` field is
expected for each settings. Currently valid values are "PROJECT" and "USER". It
is recommended to use the related constants from ``SODAR_CONSTANTS``
instead of hard coded strings.

Example of settings:

.. code-block:: python

    #: Project and user settings
    app_settings = {
        'project_bool_setting': {
            'scope': 'PROJECT',
            'type': 'BOOLEAN',
            'default': False,
            'description': 'Example project setting',
        },
        'user_str_setting': {
            'scope': 'USER',
            'type': 'STRING',
            'label': 'String example',
            'default': '',
            'description': 'Example user setting',
        },
    }

.. warning::

    Deprecation protection is place in this version for retrieving settings from
    ``project_settings`` if it has not been changed into ``app_settings`` in
    your project apps. This protection **will be removed** in the next SODAR
    Core release.


v0.5.1 (2019-04-16)
*******************

Release Highlights
==================

- Sodarcache refactoring and improvements for API, models, management and app
  config
- New default error templates

Breaking Changes
================

Site App Templates
------------------

Templates for **site apps** should extend ``projectroles/base.html``. In earlier
versions the documentation erroneously stated ``projectroles/project_base.html``
as the base template to use. Extending that document does work in this version
as long as you override the given template blocks. However, it is not
recommended and may break in the future.

Sodarcache App Changes
----------------------

The following potentially breaking changes have been made to the sodarcache app.

App configuration naming has been changed to
``sodarcache.apps.SodarcacheConfig``. Please update ``config/settings/base.py``
accordingly.

The field ``user`` has been made optional in models and the API.

An optional ``user`` argument has been added to
``ProjectAppPlugin.update_cache()``. Correspondingly, the similar argument in
``ProjectCacheAPI.set_cache_item()`` has been made optional. Please update your
plugin implementations and function calls accordingly.

The ``updatecache`` management command has been renamed to ``synccache``.

Helper get_app_names() Fixed
-----------------------------

The ``projectroles.utils.get_app_names()`` function will now return nested app
names properly instead of omitting everything beyond the topmost module.

Default Admin Setting Deprecation Removed
-----------------------------------------

The ``PROJECTROLES_ADMIN_OWNER`` setting no longer works. Use
``PROJECTROLES_DEFAULT_ADMIN`` instead.


v0.5.0 (2019-04-03)
*******************

Release Highlights
==================

- New sodarcache app for caching and aggregating data from external services
- Local user mode for site UI and remote sync
- Improved display and logging of remote project sync
- Upgrade to Bootstrap 4.3.1

Breaking Changes
================

Default Admin Setting Renamed
-----------------------------

The setting ``PROJECTROLES_ADMIN_OWNER`` has been renamed into
``PROJECTROLES_DEFAULT_ADMIN`` to better reflect its uses. Please rename this
settings variable on your site configuration to prevent issues.

.. note::

    In this release, the old settings value is still accepted in remote project
    management to avoid sudden crashes. This deprecation will be removed in the
    next release.

Bootstrap 4.3.1 Upgrade
-----------------------

The Bootstrap and Popper dependencies have been updated to the latest versions.
Please test your site to make sure this does not result in compatibility issues.
The known issue of HTML content not showing in popovers has already been fixed
in ``projectroles.js``.

Default Templates Modified
--------------------------

The default templates ``base_site.html`` and ``login.html`` have been modified
in this version. If you override them with your own altered versions, please
review the difference and update your templates as appropriate.


v0.4.5 (2019-03-06)
*******************

Release Highlights
==================

- Add user autocomplete in forms
- Allow multiple delegates per project

Breaking Changes
================

System Prerequisites
--------------------

The minimum version requirement for Django has been bumped to 1.11.20.

User Autocomplete Widget Support
--------------------------------

Due to the use of autocomplete widgets for users, the following apps must be
added into ``THIRD_PARTY_APPS`` in ``config/settings/base.py``, regardless of
whether you intend to use them in your own apps:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'dal',
        'dal_select2',
    ]

Project.get_delegate() Helper Renamed
-------------------------------------

As the limit for delegates per project is now arbitrary, the
``Project.get_delegate()`` helper function has been replaced by
``Project.get_delegates()``. The new function returns a ``QuerySet``.

Bootstrap 4 Crispy Forms Overrides Removed
------------------------------------------

Deprecated site-wide Bootstrap 4 theme overrides for ``django-crispy-forms``
were removed from the example site and are no longer supported. These
workarounds were located in ``{SITE_NAME}/templates/bootstrap4/``. Unless
specifically required forms on your site, it is recommended to remove the files
from your project.

.. note::

    If you choose to keep the files or similar workarounds in your site, you
    are responsible of maintaining them and ensuring SODAR compatibility. Such
    site-wide template overrides are outside of the scope for SODAR Core
    components. Leaving the existing files in without maintenance may cause
    undesireable effects in the future.

Database File Upload Widget
---------------------------

Within SODAR Core apps, the only known issue caused by removal of the
aforementioned Bootstrap 4 form overrides in the file upload widget of the
``django-db-file-upload`` package. If you are using the file upload package in
your own SODAR apps and have removed the site-wide Crispy overrides, you can fix
this particular widget by adding the following snippet into your form template.
Make sure to replace ``{FIELD_NAME}`` with the name of your form field.

.. code-block:: django

    {% block css %}
      {{ block.super }}
      {# Workaround for django-db-file-storage Bootstrap4 issue (#164) #}
      <style type="text/css">
        div#div_id_{FIELD_NAME} div p.invalid-feedback {
        display: block;
      }
      </style>
    {% endblock css %}

Alternatively, you can create a common override in your project-wide CSS file.


v0.4.4 (2019-02-19)
*******************

Release Highlights
==================

N/A (maintenance/bugfix release)

Breaking Changes
================

Textarea Height in Forms
------------------------

Due to this feature breaking the layout of certain third party components,
textarea height in forms is no longer adjusted automatically. An exception to
this are Pagedown-specific markdown fields.

To adjust the height of a textarea field in your forms, the easiest way is to
modify the widget of the related field in the ``__init__()`` function of your
form as follows:

.. code-block:: python

    self.fields['field_name'].widget.attrs['rows'] = 4


v0.4.3 (2019-01-31)
*******************

Release Highlights
==================

- Add display name configuration for projects and categories
- Hide immutable fields in projectroles forms

Breaking Changes
================

SODAR Constants
---------------

``PROJECT_TYPE_CHOICES`` has been removed from ``SODAR_CONSTANTS``, as it can
vary depending on implemented ``DISPLAY_NAMES``. If needed, the currently
applicable form structure can be imported from ``projectroles.forms``.


v0.4.2 (2019-01-25)
*******************

Release Highlights
==================

N/A (maintenance/bugfix release)

Breaking Changes
================

System Prerequisites
--------------------

The following minimum version requirements have been upgraded in this release:

- Django 1.11.18+
- Bootstrap 4.2.1
- JQuery 3.3.1
- Numerous required Python packages (see ``requirements/*.txt``)

Please go through your site requirements and update dependencies accordingly.
For project stability, it is still recommended to use exact version numbers for
Python requirements in your SODAR Core based site.

If you are overriding the ``projectroles/base_site.html`` in your site, make
sure to update Javascript and CSS includes accordingly.

.. note::

    Even though the recommended Python version from Django 1.11.17+ is 3.7, we
    only support Python 3.6 for this release. The reason is that some
    dependencies still exhibit problems with the most recent Python release at
    the time of writing.

ProjectAccessMixin
------------------

The ``_get_project()`` function in ``ProjectAccessMixin`` has been renamed into
``get_project()``. Arguments for the function are now optional and may be
removed in a subsequent release: ``self.request`` and ``self.kwargs`` of the
view class will be used if the arguments are not present.

Base API View
-------------

The base SODAR API view has been renamed from ``BaseAPIView`` into
``SODARAPIBaseView``.

Taskflow Backend API
--------------------

The ``cleanup()`` function in ``TaskflowAPI`` now correctly raises a
``CleanupException`` if SODAR Taskflow encounters an error upon calling its
cleanup operation. This change should not affect normally running your site, as
the function in question should only be called during Taskflow testing.


v0.4.1 (2019-01-11)
*******************

Release Highlights
==================

- Configuration updates for API and Projectroles
- Travis-CI setup

Breaking Changes
================

System Prerequisites
--------------------

Changes in system requirements:

- **Ubuntu 16.04 Xenial** is the target OS version.
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


v0.4.0 (2018-12-19)
*******************

Release Highlights
==================

- Add filesfolders app from SODAR v0.4.0
- Add bgjobs app from Varfish-Web
- Secure SODAR Taskflow API views
- Separate test server configuration for SODAR Taskflow
- Extra data variable rendering for timeline
- Additional site settings

Breaking Changes
================

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


v0.3.0 (2018-10-26)
*******************

Release Highlights
==================

- Add remote project metadata and member synchronization between multiple SODAR
  sites
- Add adminalerts app
- Add taskflowbackend app

Breaking Changes
================

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
