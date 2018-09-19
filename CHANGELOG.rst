SODAR Core Changelog
^^^^^^^^^^^^^^^^^^^^

Changelog for the SODAR Core Django app package. Loosely follows the
`Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.


v0.2.0 (2018-0-19)
==================

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

Fixed
-----

- **Timeline**
    - User model access in ``timeline.api``
    - Misaligned back button (#4)
    - Deprecated CSS in main list


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
    - ``auth_backends.py`` file for LDAP backends (omics_data_mgmt#132)
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
    - Move title bar admin and site app links to user dropdown (omics_data_mgmt#342)
    - Move project specific CSS into optionally includable ``projectroles.css``
    - Refactor and cleanup CSS
    - Move ``set_user_group()`` into ``projectroles.utils``
    - Move ``syncgroups`` management command into projectroles
    - Copy improved multi LDAP backend setup from flowcelltool (omics_data_mgmt#132)
    - Move LDAP authentication backends into projectroles (omics_data_mgmt#132)
    - Move ``login.html`` into projectroles
    - Display ``SITE_INSTANCE_TITLE`` in email instead of a hardcoded string
    - Display the first contact in ``settings.ADMINS`` in email footer
    - Use ``get_full_name()`` in email sending
    - Get site version using ``SITE_PACKAGE``
    - Get LDAP domain names to login template from settings
    - Rename custom CSS classes and HTML IDs from ``omics-*`` into ``sodar-*`` (omics_data_mgmt#166)
    - Move Shepherd theme CSS files into projectroles

Fixed
-----

- **Projectroles**
    - Tests referring to the ``filesfolders`` app not included in this project
    - ``TestHomeView.test_render()`` assumed extra SODAR system user was present (see omics_data_mgmt#367)
    - Tour link setup placing

- **Userprofile**
    - Missing user name if ``name`` field not filled in ``user_detail.html``

Removed
-------

- **Projectroles**
    - Deprecated Javascript variables ``popupWaitHtml`` and ``popupNoFilesHtml``
    - Unused template ``irods_info.html``
