SODAR Core Changelog
^^^^^^^^^^^^^^^^^^^^

Changelog for the **SODAR Core** Django app package. Loosely follows the
`Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.

Note that the issue IDs here refer to ones in the private CUBI GitLab.


Unreleased
==========

Added
-----

- **Projectroles**
    - ``TaskflowAPIAuthentication`` for handling Taskflow API auth (#47)
    - Handle ``GET`` requests for Taskflow API views (#47)

Changed
-------

- **General**
    - Upgrade minimum Python version requirement to 3.6 (#102)
    - Update and cleanup Gitlab-CI setup (#85)
    - Update Chrome Driver for UI tests
    - Cleanup Chrome setup
- **Projectroles**
    - Refactor ``BaseTaskflowAPIView`` (#47)
    - Rename Taskflow specific API views (#104)
- **Timeline**
    - Rename Taskflow specific API views (#104)

Fixed
-----

- **Projectroles**
    - Potential Django crash from auth failure in Taskflow API views


v0.4.0 (2018-12-19)
===================

Added
-----

- **General**
    - ``SODAR_API_DEFAULT_HOST`` setting for server host for API View URLs (sodar#396)
- **Bgjobs**
    - Add app from varfish-web (#95)
- **Filesfolders**
    - Add app from sodar v0.4.0 (#86)
- **Projectroles**
    - Setting ``PROJECTROLES_ENABLE_SEARCH`` (#70)
    - Re-enable "home" link in project breadcrumb (#80)
    - ``get_extra_data_link()`` in ProjectAppPluginPoint for timeline extra data (#6)
    - Allow overriding project class in ProjectAccessMixin
    - Optional disabling of categories and nesting with ``PROJECTROLES_DISABLE_CATEGORIES`` (#87)
    - Optional hiding of apps from project menus using ``PROJECTROLES_HIDE_APP_LINKS`` (#92)
    - Secure SODAR Taskflow API views with ``TASKFLOW_SODAR_SECRET`` (#46)
- **Taskflowbackend**
    - ``test_mode`` flag configured with ``TASKFLOW_TEST_MODE`` in settings (#67)
    - Submit ``sodar_secret`` for securing Taskflow API views (#46)
- **Timeline**
    - Display of extra data using ``{extra-NAME}`` (see documentation) (#6)

Changed
-------

- **General**
    - Improve list button and dropdown styles (#72)
    - Move pagedown CSS overrrides into ``projectroles.css``
    - Reduce default textarea height (#96)
- **Projectroles**
    - Make sidebar resizeable in CSS (#71)
    - Disable search if ``PROJECTROLES_ENABLE_SEARCH`` is set False (#70)
    - Allow appending custom items in project breadcrumb with ``nav_sub_project_extend`` block (#78)
    - Allow replacing project breadcrumb with ``nav_sub_project`` block (#79)
    - Disable remote site access if ``PROJECTROLES_DISABLE_CATEGORIES`` is set (#87), pending #76
    - Disable access to invite views for remote projects (#89)
    - Set "project guest" as the default role for new members (#94)
    - Make noncritical settings variables optional (#14)

Fixed
-----

- **General**
    - Potential inheritance issues in test classes (#74)
    - LDAP dependency script execution (#75)
- **Projectroles**
    - Long words in app names breaking sidebar (#71)
    - Member modification buttons visible for superuser in remote projects (#73)
    - Breadcrumb project detail link display issue in ``base.html`` (#77)
    - "None" string displayed for empty project description (#91)
    - Crash in search from empty project description


v0.3.0 (2018-10-26)
===================

Added
-----

- **General**
    - Test config and script for SODAR Taskflow testing
- **Adminalerts**
    - Add app based on SODAR v0.3.3 (#27)
    - ``TASKFLOW_TARGETS`` setting
- **Projectroles**
    - ``RemoteSite`` and ``RemoteProject`` models (#3)
    - ``RemoteSiteAppPlugin`` site plugin (#3)
    - ``PROJECTROLES_SITE_MODE`` and ``PROJECTROLES_TARGET_CREATE`` settings (#3)
    - Remote site and project management site app (#3)
    - Remote project API (#3)
    - Generic SODAR API base classes
    - ``SodarUserMixin`` for SODAR user helpers in tests
    - Optional ``readme`` and ``sodar_uuid`` args for ``_make_project()`` in tests
    - ``syncremote`` management command for calling ``RemoteProjectAPI.sync_source_data()``
    - ``get_project_by_uuid()`` and ``get_user_by_username()`` template tags
    - ``get_remote_icon()`` template tag (#3)
    - Predicates in rules for handling remote projects (#3)
    - ``ProjectModifyPermissionMixin`` for access control for remote projects (#3)
    - ``is_remote()`` and ``get_source_site()`` helpers in the ``Project`` model (#3)
    - Include template ``_titlebar_nav.html`` for additional title bar links
- **Taskflowbackend**
    - Add app based on SODAR v0.3.3 (#38)
- **Timeline**
    - ``RemoteSite`` model in ``api.get_event_description()`` (#3)

Changed
-------

- **General**
    - Update documentation for v0.3 changes, projectroles usage and fixes to v0.2 docs (#26)
- **Adminalerts**
    - Make ``ADMINALERTS_PAGINATION`` setting optional
- **Projectroles**
    - Allow ``LoggedInPermissionMixin`` to work without a permission object for superusers
    - Enable short/full title selection and remote project icon in ``get_project_link()`` template tag
    - Refactor rules
    - Disable Taskflow API views if Taskflow backend is not enabled (#37)
    - DataTables CSS and JS includes loaded in the search template (#45)
- **Timeline**
    - Minor refactoring of ``api.get_event_description()`` (#30)

Fixed
-----

- **General**
    - Pillow dependency typo in ``requirements/base.txt`` (#33)
    - Login page crash if ``AUTH_LDAP*_DOMAIN_PRINTABLE`` not found (#43)
- **Projectroles**
    - Sidebar create project visible for site apps if URL name was "create" (#36)
    - Enabling LDAP without a secondary backend caused a crash (#39)

Removed
-------

- **General**
    - iRODS specific CSS classes from ``projectroles.css``
    - App content width limit in ``projectroles.css``
    - Domain-specific Login JQuery
    - DataTables CSS and JS includes from base template (#45)


v0.2.1 (2018-09-20)
===================

Changed
-------

- **General**
    - Change ``omics_uuid`` field in all apps' models to ``sodar_uuid`` (sodar#166)
- **Projectroles**
    - Rename abstract ``OmicsUser`` model into ``SODARUser`` (sodar#166)
    - Rename ``OMICS_CONSTANTS`` into ``SODAR_CONSTANTS`` (sodar#166)
    - Rename the ``omics_constant()`` template tag into ``sodar_constant()`` (omics_data_mgmt(#166)
    - Rename ``omics_url`` in sodar_taskflow tests to ``sodar_url`` (see omics_taskflow#36)
    - Rename ``shepherd-theme-omics.css`` to ``shepherd-theme-sodar.css`` (sodar#166)


v0.2.0 (2018-09-19)
===================

Added
-----

- **General**
    - ``example_backend_app`` for a minimal backend app example
    - Backend app usage example in ``example_project_app``
- **Timeline**
    - Add timeline app based on SODAR v0.3.2 (#2)
    - App documentation

Changed
-------

- **General**
    - Update integration documentation (#1)
    - Restructure documentation files and filenames for clarity
- **Timeline**
    - Update CSS classes and overrides
    - Rename list views to ``list_project`` and ``list_objects``
    - Rename list template to ``timeline.html``
    - Refactor ``api.get_event_description()``
    - Make ``TIMELINE_PAGINATION`` optional
    - Improve exception messages in ``api.add_event()``

Fixed
-----

- **Timeline**
    - User model access in ``timeline.api``
    - Misaligned back button (#4)
    - Deprecated CSS in main list
- **Projectroles**
    - Third party apps not correctly recognized in ``get_app_names()``


v0.1.0 (2018-09-12)
===================

Added
-----

- **General**
    - Create app package for Projectroles and other reusable apps based on SODAR release v0.3.1
    - ``example_project_app`` to aid testing and work as a minimal example
    - ``example_site_app`` for demonstrating site apps
    - ``SITE_TITLE`` and ``SITE_INSTANCE_TITLE`` settings
    - ``SITE_PACKAGE`` setting for explicitly declaring site path for code
    - Documentation for integration and development
    - Separate LDAP config in ``install_ldap_dependencies.sh`` and ``requirements/ldap.txt``

- **Projectroles**
    - ``static_file_exists()`` and ``template_exists()`` helpers in common template tags
    - Abstract ``OmicsUser`` model
    - ``get_full_name()`` in abstract OmicsUser model
    - ``auth_backends.py`` file for LDAP backends (sodar#132)
    - Versioneer versioning
    - ``core_version()`` in common template tags
    - Check for footer content in ``include/_footer.html``
    - Example of the site base template in ``projectroles/base_site.html``
    - Example of project footer in ``projectroles/_footer.html``

- **Userprofile**
    - Add site app ``userprofile`` with user details
    - Display user UUID in user profile

Changed
-------

- **Projectroles**
    - Move custom modal into ``projectroles/_modal.html``
    - Check for user.name in user dropdown
    - Move content block structure and sidebar inside ``projectroles/base.html``
    - Move site title bar into optional include template ``projectroles/_site_titlebar.html``
    - Move search form into optional include template ``projectroles/_site_titlebar_search.html``
    - Make title bar dropdown inclueable as ``_site_titlebar_dropdown.html``
    - Title bar CSS and layout tweaks
    - Move ``search.js`` under projectroles
    - Move projectroles specific javascript into ``projectroles.js``
    - Move ``site_version()`` into common template tags
    - Move title bar admin and site app links to user dropdown (sodar#342)
    - Move project specific CSS into optionally includable ``projectroles.css``
    - Refactor and cleanup CSS
    - Move ``set_user_group()`` into ``projectroles.utils``
    - Move ``syncgroups`` management command into projectroles
    - Copy improved multi LDAP backend setup from flowcelltool (sodar#132)
    - Move LDAP authentication backends into projectroles (sodar#132)
    - Move ``login.html`` into projectroles
    - Display ``SITE_INSTANCE_TITLE`` in email instead of a hardcoded string
    - Display the first contact in ``settings.ADMINS`` in email footer
    - Use ``get_full_name()`` in email sending
    - Get site version using ``SITE_PACKAGE``
    - Get LDAP domain names to login template from settings
    - Rename custom CSS classes and HTML IDs from ``omics-*`` into ``sodar-*`` (sodar#166)
    - Move Shepherd theme CSS files into projectroles

Fixed
-----

- **Projectroles**
    - Tests referring to the ``filesfolders`` app not included in this project
    - ``TestHomeView.test_render()`` assumed extra SODAR system user was present (see sodar#367)
    - Tour link setup placing

- **Userprofile**
    - Missing user name if ``name`` field not filled in ``user_detail.html``

Removed
-------

- **Projectroles**
    - Deprecated Javascript variables ``popupWaitHtml`` and ``popupNoFilesHtml``
    - Unused template ``irods_info.html``
