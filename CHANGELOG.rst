SODAR Core Changelog
^^^^^^^^^^^^^^^^^^^^

Changelog for the **SODAR Core** Django app package. Loosely follows the
`Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.

Note that the issue IDs here refer to ones in the private CUBI GitLab.


Unreleased
==========

Added
-----

- **General**
    - SAML SSO authentication support (#588)
    - REST API example ``HelloExampleProjectAPIView`` in ``example_project_app`` (#518)
- **Projectroles**
    - Projectroles app settings (#532)
    - Remote sync for projectroles app setting (#533, #586)
    - IP address based access restriction for projects (#531)
    - ``is_delegate()`` and ``is_owner_or_delegate()`` helpers for ``Project`` model
    - Remote sync for non-owner category members (#502)
    - ``setting_delete()`` function to ``AppSettingAPI`` (#538)
    - ``cleanappsettings`` management command (#374)
    - ``exclude_inherited`` argument in ``Project.get_delegates()`` (#595)
    - Optional options for app settings of type ``STRING`` and ``INTEGER`` (#592)
    - Display placeholders for app setting form fields (#584)

Changed
-------

- **General**
    - Replace development helper scripts with ``Makefile`` (#135)
    - Upgrade to Bootstrap v4.5.3 and jQuery v3.5.1 (#563)
    - Upgrade to Chromedriver v87
    - Upgrade general Python requirements (#576)
    - Migrate GitHub CI from Travis to GitHub actions (#577)
- **Projectroles**
    - Allow updating local app settings on a ``TARGET`` site (#545)
    - Refactor project list filtering (#566)
    - Move project list javascript to ``project_list.js`` (#566)
    - Rename owner role transfer URL pattern and timeline event (#590)
- **Userprofile**
    - Cosmetic updates for user detail template (#600)

Fixed
-----

- **Projectroles**
    - Invite redirect not working in Add Member view (#589)
    - Wrong role label displayed for category owner/delegate in member list (#593)
    - Django settings access in ``forms`` and ``serializers``
    - Delegate limit check broken by existing delegate roles of inherited owners (#595)

Removed
-------

- **General**
    - Travis CI setup in ``.travis.yml`` (#577)
- **Projectroles**
    - Template ``_project_filter_item.html`` (#566)
    - Template tag ``get_project_list()`` (#566)


v0.8.4 (2020-11-12)
===================

Changed
-------

- **General**
    - Documentation updates for JOSS submission


v0.8.3 (2020-09-28)
===================

Added
-----

- **General**
    - Missing migration for the ``SODARUser`` model (#581)

Changed
-------

- **General**
    - Upgrade to Chromedriver v85 (#569)
- **Projectroles**
    - Improve project list header legend (#571)
    - Make ``sync_source_data()`` atomic
    - Prevent creation of local projects under remote categories (#583)
- **Siteinfo**
    - Refactor app plugin statistics retrieval (#573)

Fixed
-----

- **General**
    - Invalid statement in ``setup_database.sh`` (#580)
- **Projectroles**
    - Missing exception handling for ``sync_source_data()`` calls (#582)
    - Crash from conflicting local category structure (#582)
- **Siteinfo**
    - Crash from exceptions raised by app plugin ``get_statistics()`` (#572)
- **Timeline**
    - CSS for ``sodar-tl-link-detail`` links (#578)

Removed
-------

- **General**
    - Unused ``Pillow`` dependency (#575)


v0.8.2 (2020-07-22)
===================

Added
-----

- **Bgjobs**
    - Enable site-wide background jobs (#544)
    - Site app plugin for site-wide background jobs (#544)
- **Projectroles**
    - ``sodar-header-button`` CSS class (#550)
    - Logging for ``AppSettingAPI`` (#559)

Changed
-------

- **Projectroles**
    - Upgrade to Chromedriver v83 (#543)
    - Rename ``is_app_link_visible()`` template tag into ``is_app_visible()`` (#546)
    - Refactor project list to reduce queries and template tag use (#551, #567)

Fixed
-----

- **Projectroles**
    - Transferring project ownership to inherited owner not allowed (#534)
    - Uniqueness constraint in ``AppSetting`` incompatible with ``PROJECT_USER`` scope settings (#542)
    - Inherited owner email address not displayed in project member list (#541)
    - App visibility check broken in ``project_detail.html`` (#546)
    - Invite accept for a category invoking Taskflow and causing a crash (#552)
    - Project form ``parent`` forced to wrong value if user lacks role in parent category (#558)
    - Invalid ``app_name`` not handled in ``AppSettingAPI.get_default_setting()`` (#560)
    - Empty JSON and false boolean app settings not set in project form (#557)
    - Minor Javascript errors thrown by ``projectroles.js`` (#536)
    - Long lines breaking email preview layout (#564)


v0.8.1 (2020-04-24)
===================

Added
-----

- **Projectroles**
    - CSS class ``sodar-pr-project-list-custom`` for custom project list items (#525)

Fixed
-----

- **Projectroles**
    - CSS padding issue with ``sodar-list-btn`` and Chrome (#529, sodar#844)
    - Crash from missing optional setting ``PROJECTROLES_DISABLE_CATEGORIES`` (#524)
    - Remote project editing not prevented in REST API views (#523)

Removed
-------

- **Projectroles**
    - Deprecated ``SODARAPIObjectInProjectPermissions`` base class (#527)


v0.8.0 (2020-04-08)
===================

Added
-----

- **General**
    - "For the Impatient" section in docs
- **Filesfolders**
    - API views for file, folder and hyperlink management (#443)
- **Projectroles**
    - Import new REST API view base classes from SODAR (#48, #461)
    - Import base serializers from SODAR (#462)
    - API views for project and role management (#48, #450)
    - ``projectroles.tests.test_views_api.TestAPIViewsBase`` for API view testing (#48)
    - ``SODARAPIPermissionTestMixin`` for API view permission tests
    - New helper methods in ``SODARAPIViewTestMixin``
    - Provide live server URL for Taskflow in ``TestTaskflowBase.request_data`` (#479)
    - ``TestTaskflowAPIBase`` for testing API views with SODAR Taskflow (#488)
    - Permission tests using Knox tokens (#476)
    - Base Ajax view classes in ``projectroles.views_ajax`` (#465)
    - Allow assigning roles for categories (#463)
    - Allow displaying project apps in categories with ``category_enable`` (#447)
    - Allow category delegates and owners to create sub-categories and projects (#464)
    - ``get_role_display_name()`` helper in ``projectroles_common_tags`` (#505)
    - ``get_owners()``, ``is_owner()`` and ``get_all_roles()`` helpers for ``Project`` (#464)
    - Allow using legacy UI test login method with ``PROJECTROLES_TEST_UI_LEGACY_LOGIN`` (#509)
    - Allow moving categories and projects under different categories (#512)
    - ``SODARForm`` and ``SODARModelForm`` base classes for forms
    - Enable retrieving flat recursive list of children objects in ``Project.get_children()``
    - Support for ``data`` in permission test ``assert_response()`` method (#155)
- **Taskflowbackend**
    - ``get_inherited_roles()`` helper (#464)
- **Timeline**
    - ``get_models()`` helper
- **Tokens**
    - Add app from varfish-web (#452)

Changed
-------

- **General**
    - Upgrade minimum Django version to v1.11.29 (#520)
    - Upgrade JQuery to v3.4.1 (#519)
    - Upgrade Bootstrap to v4.4.1 (#460)
    - General upgrade for Python package requirements (#124, #459)
    - Reorganize view classes and URL patterns (#480)
    - Refactor Ajax views (#465, #475)
    - Update ``CONTRIBUTING.rst``
    - Use ``SODARForm`` and ``SODARModelForm`` base classes in forms
- **Projectroles**
    - Suppress peer site removal logging if nothing was removed (#478)
    - Refactor ``SODARCoreAPIBaseView`` into ``SODARCoreAPIBaseMixin`` (#461)
    - Allow providing single user to ``assert_response()`` in permission tests (#474)
    - Move ``SODARAPIViewTestMixin`` into ``test_views_api`` and rename (#471)
    - Move ``KnoxAuthMixin`` functionality into ``SODARAPIViewTestMixin``
    - ``get_accept_header()`` in API tests returns header as dict
    - Refactor base permission test classes (#490)
    - Move ``utils.set_user_group()`` to ``SODARUser.set_group()`` (#483)
    - Call ``set_group()`` in ``SODARUser.save()`` (#483)
    - Replace ``projectroles_tags.is_app_hidden()`` with ``is_app_link_visible()``
    - Inherit owner permissions from parent categories (#464)
    - Refactor project roles template (#505)
    - Disable owner updating in project update form (#508)
    - Allow updating project parent via SODAR Taskflow (#512)
- **Taskflowbackend**
    - Refactor ``synctaskflow`` management command and add logging
- **Timeline**
    - Display app for categories (#447)

Fixed
-----

- **General**
    - Duplicate ``contributing.rst`` redirection file in docs (#481)
    - ``.tox`` not ignored in ``black.sh``
    - Coverage checks in Travis-CI (#507)
- **Projectroles**
    - Swapping owner and delegate roles not allowed if at delegate limit (#477)
    - Remote sync for owner role failing with specific user order in data (#439)
    - Redundant updating of ``Project.submit_status`` during project creation
    - Make ``test_widget_user_options()`` more reliable (#253)
    - Missing permission check by role type in ``RoleAssignmentDeleteView.post()`` (#492)
    - Unordered queryset warnings from the ``User`` model (#494)
    - Incorrect user iteration in ``test_user_autocomplete_ajax()`` (#469)
    - Redundant input validation preventing search with valid characters (#472)
    - Local users disabled in local development configuration (#500)
    - Member link not visible in responsive project dropdown (#466)
    - CSS issues with Bootstrap 4.4.1 in search pagination (#372, #460)
    - Raise ``ImproperlyConfigured`` for missing parameters in ``ProjectAccessMixin`` (#516)
- **Timeline**
    - CSS issues with Bootstrap 4.4.1 (#460)

Removed
-------

- **Projectroles**
    - ``SODARAPIBaseView`` base class, replaced by API view mixins (#461)
    - ``KnoxAuthMixin`` from view tests
    - ``get_selectable_users()`` from ``forms``
    - Redundant render/redirect helpers from ``TestPermissionBase``: use ``assert_response()`` instead (#484)
    - ``APIPermissionMixin`` for API views: use base API/Ajax view classes instead (#467)
    - ``is_app_hidden()`` from ``projectroles_tags``


v0.7.2 (2020-01-31)
===================

Added
-----

- **Projectroles**
    - ``custom_order`` argument in ``get_active_plugins()`` (#431)
    - Enable ordering custom project list columns in project app plugin (#427)
    - ``SODARCoreAPIBaseView`` base API view class for internal SODAR Core apps (#442)
    - API version enforcing in ``RemoteProjectsSyncView`` and ``syncremote.py`` (#444)
    - Allow extra keyword arguments in ``get_backend_api()`` (#397)
    - Example usage of ``get_backend_api()`` extra kwargs in ``example_backend_app`` (#397)
    - ``SODARUserChoiceField`` and ``get_user_widget()`` for user selection in forms (#455)
    - Setting ``reply-to`` headers for role change and invite emails (#446)
    - No reply note and related ``PROJECTROLES_EMAIL_SENDER_REPLY`` setting (#446)
    - Display hidden project app settings to superusers (#424)
- **Sodarcache**
    - Allow limiting ``deletecache`` to a specific project (#448)

Changed
-------

- **General**
    - Upgrade minimum Django version to 1.11.27
    - Base ``RemoteProjectGetAPIView`` on ``SODARCoreAPIBaseView`` (#442)
    - Upgrade to Chromedriver v80 (#510)
- **Bgjobs**
    - Make ``specialize_job()`` more robust (#456)
- **Projectroles**
    - Accept null value for ``AppSetting.value_json`` (#426)
    - Use ``PluginContextMixin`` in ``ProjectContextMixin`` (#430)
    - Move ``get_accept_header()`` to ``SODARAPIViewMixin`` (#445)
    - Allow exceptions to be raised by ``get_backend_plugin()`` (#451)
    - Improve tour help CSS (#438)
    - Field order in ``RoleAssignmentOwnerTransferView`` (#441)
    - Redesign user autocomplete handling in forms (#455)
    - Rename ``SODARUserAutocompleteWidget`` and ``SODARUserRedirectWidget`` (#455)
    - Disable ownership transfer link if owner is the only project user (#454)

Fixed
-----

- **Projectroles**
    - Potential crash in ``_project_header.html`` with ownerless kiosk mode category (#422)
    - Form crash when saving a JSON app setting with ``user_modifiable=False`` (#426)
    - Inconsistent plugin ordering in custom project list columns (#428)
    - Project app plugins included twice in ``HomeView`` (#432)
    - ``ProjectPermissionMixin`` query set override with ``get_project_filter_key()``
    - Search disabled with unchanged input value on search page load (#436)
    - Subprojects queried for non-categories in ``project_detail.html`` (#434)
    - Current owner selectable in ownership transfer form (#440)
- **Taskflowbackend**
    - Potential crash in ``TaskflowAPI`` initialization

Removed
-------

- **Projectroles**
    - Unused backend plugins queried for context data in ``HomeView`` (#433)
    - Unneeded ``UserAutocompleteExcludeMembersAPIView`` (#455)


v0.7.1 (2019-12-18)
===================

Added
-----

- **General**
    - Include CHANGELOG in documentation (#379)
- **Projectroles**
    - ``widget_attrs`` parameter for project and user settings (#404)
    - Remote project member management link for target projects (#382)
    - Current user in ``get_project_list_value()`` arguments (#413)
    - Display category owner in page header (#414)
    - Configuring UI test settings via Django settings or ``TestUIBase`` vars (#417)
    - Initial support for deploying site in kiosk mode (#406)
    - Optional disabling of default CDN Javascript and CSS includes (#418)
    - Defining custom global JS/CSS includes in Django settings (#418)

Changed
-------

- **General**
    - Change "Breaking Changes" doc into "Major Changes" (#201)
    - Refactor and rename ownership transfer classes and template
    - Use RTD theme in documentation (#384)
    - Upgrade to Chromedriver v79
- **Adminalerts**
    - Rename ``INACTIVE`` alert state in UI (#396)
    - Rename URL name and pattern for activation API view (#378)
    - Improve alert detail page layout (#385)
- **Projectroles**
    - Improve unsupported browser warning (#405)
    - Move project list description into tooltip (#388)
- **Siteinfo**
    - Improve page title and heading (#402)
- **Sodarcache**
    - Clarify management command logging (#403)
- **Timeline**
    - Improve extra data status tab legend (#380)

Fixed
-----

- **General**
    - PPA used for Python 3.6 installs no longer available (#416)
- **Filesfolders**
    - Invalid HTML in project list extra columns
- **Projectroles**
    - Dismissing login error alert in ``login.html`` not working (#377)
    - Current owner queries incorrectly filtered in ``RoleAssignmentOwnerTransferView`` (#393)
    - Hardcoded project type display name in sent emails (#398)
    - Silent failing of invalid app setting type in plugin definition (#390)
    - Exception raised by hidden sidebar in sidebar height calculation (#407)
    - Crash in ``get_default_setting()`` if default JSON value was not set (#389)
    - Owner widget hidden in category update view (#394)
    - Project list extra column header alignment not set (#412)
    - ``get_project_list_value()`` template tag displaying "None" on null value (#411)


v0.7.0 (2019-10-09)
===================

Added
-----

- **General**
    - Development env file example ``env.example`` (#297)
    - Postgres database development setup script (#302)
    - ``ENABLE_DEBUG_TOOLBAR`` setting for local development (#349)
    - ``local_target2.py`` config for peer remote site development (#200)
- **Adminalerts**
    - Activate/suspend button in alert list (#42)
- **Bgjobs**
    - Pagination for background job list (#335)
    - ``BGJOBS_PAGINATION`` Django setting (#335)
- **Projectroles**
    - ``get_backend_include()`` common template tag (#261)
    - ``css_url`` member variable in ``BackendPluginPoint`` (#261)
    - Example of on-demand Javascript/CSS inclusion in example apps (#261)
    - Remote project link display toggle for target sites (#276)
    - Project UUID clipboard copying button (#290)
    - Support for app settings in site apps (#308)
    - Initial implemenetation for common clipboard copying visualization (#333)
    - Send email for owner role assignment (#325)
    - Common pagination include template ``_pagination.html`` (#334)
    - Synchronization and display of ``PEER`` sites in remote site management (#200)
    - Link for copying remote site secret token in remote site list (#332)
    - Project ownership transfer from member list (#287)
    - UI notification for disabled member management on target sites (#301)
    - Management command ``addremotesite`` for adding remote sites (#314)
    - JSON support for app settings (#268)
    - ``get_setting_def()`` in app settings API
    - Timeline logging of app settings in project creation (#359)
    - "Project and user" scope for app settings (#266)
    - ``REVOKED`` status for remote projects with revoked access (#327)
    - ``Project.is_revoked()`` helper (#327)
    - Disabling access for non-owner/delegate for revoked projects in ``ProjectPermissionMixin`` (#350)
- **Timeline**
    - Display event extra data as JSON (#6)
- **Userprofile**
    - User setting for project UUID clipboard copying (#290, #308)

Changed
-------

- **General**
    - Upgrade Chromedriver to version 77.0.3865.40
    - Use ``CurrentUserFormMixin`` instead of repeated code (#12)
    - Run tests in parallel where applicable
    - Upgrade minimum Django version to 1.11.25 (#346)
    - General upgrade for Python package requirements (#282)
- **Adminalerts**
    - Use common pagination template
- **Projectroles**
    - Improve user name placeholder in ``login.html`` (#294)
    - Backend app Javascript and CSS included on-demand instead of for all templates (#261)
    - Make sidebar hiding dynamic by content height (#316)
    - Replace ``login_and_redirect()`` in UI tests with a faster cookie based function (#323)
    - Refactor remote project display on details page (#196)
    - Refactor AppSettingAPI (#268)
    - Enable calling ``AppSettingAPI.get_setting_defs()`` with app name instead of plugin object
    - Use ``ProjectPermissionMixin`` on project detail page (#350)
- **Timeline**
    - Use common pagination template (#336)

Fixed
-----

- **Projectroles**
    - Output of template tag ``get_project_link()``
    - Redundant inheritance in ``CurrentUserFormMixin`` (#12)
    - Trailing slashes not parsed correctly in remote project URLs (#319)
    - Crash in ``get_project_column_count()`` with no active project app plugins (#320)
    - UI test helper ``build_selenium_url()`` refactored to work with Chrome v77 (#337)
    - Disallow empty values in ``RemoteSite.name``
    - Remote sync of parent category roles could fail with multiple subprojects
    - ``RemoteProject`` modifications not saved during sync update
    - Timeline events not created in remote project sync (#370)
    - DAL select modifying HTML body width (#365)
    - Footer overflow breaking layout (#367, #375)
- **Timeline**
    - Crash from exception raised by ``get_object_link()`` in a plugin (#328)

Removed
-------

- **Projectroles**
    - Duplicate database indexes from ``RoleAssignment`` (#285)
    - Deprecated ``get_setting()`` tag from ``projectroles_common_tags`` (#283)
    - Project owner change from project updating form (#287)
    - ``ProjectSettingMixin`` from ``projectoles.tests.test_views`` (#357)


v0.6.2 (2019-06-21)
===================

Added
-----

- **General**
    - Badges for Readthedocs documentation and Zenodo DOI (#274)
- **Bgjobs**
    - ``BackgroundJobFactory`` for tests from Varfish-web
- **Projectroles**
    - Unit test to assure owner user creation during project update when using SODAR Taskflow (sodar_taskflow#49)
    - Common template tag ``get_app_setting()`` (#281)
    - Hiding app settings from forms with ``user_modifiable`` (#267)
    - ``AppSetting.value_json`` field (#268)
- **Sodarcache**
    - Logging in ``delete_cache()`` (#279)
- **Userprofile**
    - Support for ``AppSetting.user_modifiable`` (#267)

Changed
-------

- **General**
    - Upgrade minimum Django version to 1.11.21 (#278)
- **Projectroles**
    - ``get_setting()`` template tag renamed into ``get_django_setting()`` (#281)
    - Implement project app descriptions on details page with ``get_info_link()`` (#277)

Fixed
-----

- **General**
    - Documentation sections for Readthedocs


v0.6.1 (2019-06-05)
===================

Added
-----

- **Filesfolders**
    - Example project list columns (#265)
    - Setting ``FILESFOLDERS_SHOW_LIST_COLUMNS`` to manage example project list columns (#265)
- **Projectroles**
    - Optional project list columns for project apps (#265)
- **Sodarcache**
    - ``delete_cache()`` API function (#257)

Changed
-------

- **Projectroles**
    - Refactor ``RemoteProject.get_project()`` (#262)
    - Use ``get_info_link()`` in remote site list (#264)
    - Define ``SYSTEM_USER_GROUP`` in ``SODAR_CONSTANTS`` (#251)
    - Make pagedown textarea element resizeable and increase minimum height (#273)
- **Sodarcache**
    - Handle and log raised exceptions in ``synccache`` management command (#272)
- **Userprofile**
    - Disable user settings link if no settings are available (#260)

Fixed
-----

- **General**
    - Chrome and Chromedriver version mismatch in Travis-CI config (#254)
- **Projectroles**
    - Remove redundant ``get_project_list()`` call from ``project_detail.html``

Removed
-------

- **Projectroles**
    - Unused project statistics in the home view (#269)
    - App settings deprecation protection (#245)
- **Sodarcache**
    - Unused ``TaskflowCacheUpdateAPIView`` (#205)


v0.6.0 (2019-05-10)
===================

Added
-----

- **Filesfolders**
    - Provide app statistics for siteinfo (#18)
- **Projectroles**
    - User settings for settings linked to users instead of projects (#16)
    - ``user_settings`` field in project plugins (#16)
    - Optional ``label`` key for settings
    - Optional "wait for element" args in UI test helpers to ease Javascript testing (#230)
    - ``get_info_link()`` template tag (#239)
    - ``get_setting_defs()`` API function for retrieving project and user setting definitions (#225)
    - ``get_all_defaults()`` API function for retrieving all default setting values (#225)
    - Human readable labels for app settings (#9)
- **Siteinfo**
    - Add app for site info and statistics (#18)
- **Sodarcache**
    - Optional ``--project`` argument for the ``synccache`` command (#232)
- **Timeline**
    - Provide app statistics for siteinfo (#18)
- **Userprofiles**
    - View and form for displaying and updating user settings (#16)

Changed
-------

- **General**
    - Upgrade to ChromeDriver v74 (#221)
- **Bgjobs**
    - Job order to match downstream Varfish
- **Filesfolders**
    - Update app settings (#246)
- **Projectroles**
    - Rename ``project_settings`` module to ``app_settings`` (#225)
    - App settings API updated to support project and user settings (#225)
    - Write an empty dict for ``app_settings`` by default

Fixed
-----

- **Bgjobs**
    - Date formatting in templates (#220)
- **Sodarcache**
    - Crash from ``__repr__()`` if project not set (#223)
    - Broken backend plugin icon (#250)

Removed
-------

- **Timeline**
    - Unused and deprecated project settings (#246)


v0.5.1 (2019-04-16)
===================

Added
-----

- **General**
    - Bgjobs/Celery updates from Kiosc (#175)
    - Default error templates in ``projectroles/error/*.html`` (#210)
- **Projectroles**
    - Optional ``user`` argument in ``ProjectAppPlugin.update_cache()`` (#203)
    - Migration for missing ``RemoteProject`` foreign keys (#197)
- **Sodarcache**
    - API logging (#207)
    - Indexing of identifying fields (#218)

Changed
-------

- **General**
    - Extend ``projectroles/base.html`` for all site app templates, update docs (#217)
    - Use projectroles error templates on the example site (#210)
- **Sodarcache**
    - Make ``user`` field optional in models and API (#204)
    - Rename app configuration into ``SodarcacheConfig`` to follow naming conventions (#202)
    - Rename ``updatecache`` management command to ``synccache`` (#208)

Fixed
-----

- **General**
    - Add missing curl dependency in ``install_os_dependencies.sh`` (#211)
    - Django debug toolbar not displayed when using local configuration (#213)
- **Projectroles**
    - Nested app names not properly returned by ``utils.get_app_names()`` (#206)
    - Forced width set for all Bootstrap modals in ``projectroles.css`` (#209)
    - Long category paths breaking remote project list (#84)
    - Incorrect table rows displayed during project list initialization (#212)
    - Field ``project`` not set for source site ``RemoteProject`` objects (#197)
    - Crash from ``project_base.html`` in site app if not overriding title block (#216)

Removed
-------

- **General**
    - Django debug toolbar workarounds from ``project.css`` and ``project.scss`` (#215)
- **Projectroles**
    - ``PROJECTROLES_ADMIN_OWNER`` deprecation protection: use ``PROJECTROLES_DEFAULT_ADMIN`` (#190)


v0.5.0 (2019-04-03)
===================

Added
-----

- **Projectroles**
    - Warning when using an unsupported browser (#176)
    - Setting ``PROJECTROLES_BROWSER_WARNING`` for unsupported browser warning (#176)
    - Javascript-safe toggle for ``get_setting()`` template tag
    - ID attributes in site containers (#173)
    - Setting ``PROJECTROLES_ALLOW_LOCAL_USERS`` for showing and syncing non-LDAP users (#193)
    - Allow synchronizing existing local target users for remote projects (#192)
    - Allow selecting local users if in local user mode (#192)
    - ``RemoteSite.get_url()`` helper
    - Simple display of links to project on external sites in details page (#182)
- **Sodarcache**
    - Create app (#169)

Changed
-------

- **General**
    - Upgrade to Bootstrap 4.3.1 and Popper 1.14.7 (#181)
- **Projectroles**
    - Improve remote project sync logging (#184, #185)
    - Rename ``PROJECTROLES_ADMIN_OWNER`` into ``PROJECTROLES_DEFAULT_ADMIN`` (#187)
    - Update login template and ``get_login_info()`` to support local user mode (#192)

Fixed
-----

- **Projectroles**
    - Crash in ``get_assignment()`` if called with AnonymousUser (#174)
    - Line breaks in templates breaking ``badge-group`` elements (#180)
    - User autocomplete for users with no group (#199)

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
