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
    - Warning when using an unsupported browser (#176)
    - Setting ``PROJECTROLES_BROWSER_WARNING`` for unsupported browser warning (#176)
    - Javascript-safe toggle for ``get_setting()`` template tag
    - ID attributes in site containers (#173)

Fixed
-----

- **Projectroles**
    - Crash in ``get_assignment()`` if called with AnonymousUser (#174)

Removed
-------

- **General**
    - Deprecated Bootstrap 4 workaround from ``project.js`` (#178)


v0.4.5 (2019-03-06)
===================

Added
-----

- **Projectroles**
    - User autocomplete widgets (#51)
    - Logging in ``syncgroups`` and ``syncremote`` management commands
    - ``PROJECTROLES_DELEGATE_LIMIT`` setting (#21)

Changed
-------

- **General**
    - Upgrade minimum Django version to 1.11.20 (#152)
    - Use user autocomplete in forms in place of standard widget (#51)
- **Filesfolders**
    - Hide parent folder widgets in item creation forms (#159)
- **Projectroles**
    - Enable allowing multiple delegates per project (#21)

Fixed
-----

- **Filesfolders**
    - File upload wiget error not displayed without Bootstrap 4 workarounds (#164)
- **Projectroles**
    - Potential crash in ``syncremote`` if run as Celery job (#160)

Removed
-------

- **General**
    - Old Bootstrap 4 workarounds for django-crispy-forms (#157)


v0.4.4 (2019-02-19)
===================

Changed
-------

- **Projectroles**
    - Modify ``modifyCellOverflow()`` to work with non-table containers (#149)
    - Non-Pagedown form textarea height no longer adjusted automatically (#151)

Fixed
-----

- **Projectroles**
    - Crash in remote project sync caused by typo in ``remoteproject_sync.html`` (#148)
    - Textarea element CSS override breaking layout in third party components (#151)


v0.4.3 (2019-01-31)
===================

Added
-----

- **General**
    - Codacy badge in ``README.rst`` (#140)
- **Projectroles**
    - Category and project display name configuration via ``SODAR_CONSTANTS`` (#141)
    - ``get_display_name()`` utils function and template tag to retrieve ``DISPLAY_NAMES`` (#141)
    - Django admin link warning if taskflowbackend is enabled

Changed
-------

- **General**
    - Use ``get_display_name()`` to display category/project type (#141)
- **Projectroles**
    - Hide immutable fields in forms (#142)
    - Rename Django admin link in user dropdown

Fixed
-----

- **Projectroles**
    - View access control for categories (#143)

Removed
-------

- **General**
    - Redundant ``rules.is_superuser`` predicates from rules (#138)
- **Projectroles**
    - ``get_project_type()`` template tag (use ``get_display_name()`` instead)
    - Unused template ``_roleassignment_import.html``
    - ``PROJECT_TYPE_CHOICES`` from ``SODAR_CONSTANTS``
    - ``force_select_value()`` helper no longer used in forms (#142)


v0.4.2 (2019-01-25)
===================

Added
-----

- **General**
    - Flake8 and Codacy coverage in Travis-CI (#122)
    - Flake8 in GitLab-CI (#127)
- **Projectroles**
    - Automatically pass CSRF token to unsafe Ajax HTTP methods (#116)
    - Queryset filtering in ``ProjectPermissionMixin`` from digestiflow-web (#134)
    - Check for ``get_project_filter_key()`` from digestiflow-web (#134)

Changed
-------

- **General**
    - Upgrade minimum Django version to 1.11.18 (#120)
    - Upgrade Python dependencies (#123)
    - Update .coveragerc
    - Upgrade to Bootstrap 4.2.1 (#23)
    - Upgrade to JQuery 3.3.1 (#23)
    - General code cleanup
    - Code formatting with Black (#133)
- **Filesfolders**
    - Refactor ``BatchEditView`` and ``FileForm.clean()`` (#128)
- **Projectroles**
    - Use ``alert-dismissable`` to dismiss alerts (#13, #130)
    - Update DataTables dependency in ``search.html`` template
    - Refactor ``ProjectModifyMixin`` and ``RemoteProjectAPI`` (#128)
    - Disable ``USE_I18N`` in example site settings (#117)
    - Refactor ``ProjectAccessMixin._get_project()`` into ``get_project()`` (#134)
    - Rename ``BaseAPIView`` into ``SODARAPIBaseView``
- **Timeline**
    - Refactor ``get_event_description()`` (#30, #128)

Fixed
-----

- **General**
    - Django docs references (#131)
- **Projectroles**
    - ``sodar-list-dropdown`` layout broke down with Bootstrap 4.2.1 (#23)
    - ``TASKFLOW_TEST_MODE`` not checked for allowing SODAR Taskflow tests (#126)
    - Typo in ``update_remote`` timeline event description (#129)
    - Textarea height modification (#125)
    - Text wrapping in ``sodar-list-btn`` and ``sodar-list-dropdown`` with Bootstrap 4.2.1 (#132)
- **Taskflowbackend**
    - ``TASKFLOW_TEST_MODE`` not checked for allowing ``cleanup()`` (#126)
    - ``FlowSubmitException`` raised instead of ``CleanupException`` in ``cleanup()``

Removed
-------

- **General**
    - Legacy Python2 ``super()`` calls (#118)
- **Projectroles**
    - Custom alert dismissal script (#13)
- **Example Site App**
    - Example file ``test.py``


v0.4.1 (2019-01-11)
===================

Added
-----

- **General**
    - Travis-CI configuration (#90)
- **Adminalerts**
    - Option to display alert to unauthenticated users with ``require_auth`` (#105)
- **Projectroles**
    - ``TaskflowAPIAuthentication`` for handling Taskflow API auth (#47)
    - Handle ``GET`` requests for Taskflow API views (#47)
    - API version settings ``SODAR_API_ALLOWED_VERSIONS`` and ``SODAR_API_MEDIA_TYPE`` (#111)
    - Site app support in ``change_plugin_status()``
    - ``get_sodar_constants()`` helper (#112)
- **Taskflowbackend**
    - API logging

Changed
-------

- **General**
    - Upgrade minimum Python version requirement to 3.6 (#102)
    - Update and cleanup Gitlab-CI setup (#85)
    - Update Chrome Driver for UI tests
    - Cleanup Chrome setup
    - Enable site message display in login view (#105)
    - Cleanup and refactoring for public GitHub release (#90)
    - Drop support for Ubuntu Jessie and Trusty
    - Update installation utility scripts (#90)
- **Filesfolders**
    - Move inline javascript into ``filesfolders.js``
- **Projectroles**
    - Refactor ``BaseTaskflowAPIView`` (#47)
    - Rename Taskflow specific API views (#104)
    - Unify template tag names in ``projectroles_tags``
    - Change default SODAR API media type into ``application/vnd.bihealth.sodar-core+json`` (#111)
    - Allow importing ``SODAR_CONSTANTS`` into settings for modification (#112)
    - Move ``SODAR_CONSTANTS`` to ``constants.py`` (#112)
- **Timeline**
    - Rename Taskflow specific API views (#104)

Fixed
-----

- **Filesfolders**
    - Overwrite check for zip archive upload if unarchiving was unset (#113)
- **Projectroles**
    - Potential Django crash from auth failure in Taskflow API views
    - Timeline description for updating a remote project
    - Project update with Taskflow failure if description not set (#110)
- **Timeline**
    - ``TaskflowEventStatusSetAPIView`` skipping ``sodar_token`` check (#109)

Removed
-------

- **Filesfolders**
    - Unused dropup app buttons mode in templates (#108)
- **Projectroles**
    - Unused arguments in ``email`` API
    - Unused static file ``shepherd-theme-default.css``
    - Disabled role importing functionality (#61, pending #17)
    - Unused dropup app buttons mode in templates (#108)
- **Timeline**
    - ``ProjectEventStatus.get_timestamp()`` helper


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
    - Rename the ``omics_constant()`` template tag into ``sodar_constant()`` (sodar#166)
    - Rename ``omics_url`` in sodar_taskflow tests to ``sodar_url`` (see sodar_taskflow#36)
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
