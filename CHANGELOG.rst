SODAR Projectroles Changelog
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Changelog for the SODAR Projectroles Django app package. Loosely follows the
`Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`_ guidelines.


Unreleased
==========

Added
-----

- Create app package for Projectroles based on SODAR release v0.3.1
- ``example_project_app`` to aid testing and work as a minimal example
- ``static_file_exists()`` helper in common template tags
- ``SITE_TITLE`` and ``SITE_INSTANCE_TITLE`` settings
- ``example_site_app`` for demonstrating site apps
- ``get_full_name()`` in User model
- Abstract ``OmicsUser`` model
- ``user_backends.py`` file for LDAP backends (omics_data_mgmt#132)
- ``SITE_MODULE`` setting for explicitly declaring site path for code
- Versioneer versioning for projectroles
- ``projectroles_version()`` in common template tags

Changed
-------

- Move custom modal into ``projectroles/_modal.html``
- Check for user.name in user dropdown
- Move content block structure and sidebar inside ``projectroles/base.html``
- Move search form into optional include template ``projectroles/_search_form.html``
- Move site title bar into optional include template ``projectroles/_site_titlebar.html``
- Title bar CSS and layout tweaks
- Move ``search.js`` under projectroles
- Move projectroles specific javascript into ``projectroles.js``
- Move ``site_version()`` into common template tags
- Move footer content into ``include/_footer.html``
- Move title bar admin and site app links to user dropdown (omics_data_mgmt#342)
- Move project specific CSS into optionally includable ``projectroles.css``
- Refactor and cleanup CSS
- Move template ``user_detail.html`` into projectroles
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

Fixed
-----

- Tests referring to the ``filesfolders`` app not included in this project
- ``TestHomeView.test_render()`` assumed extra SODAR system user was present (see omics_data_mgmt#367)
- Tour link setup placing
- Missing user name if ``name`` field not filled in ``user_detail.html``

Removed
-------

- Deprecated Javascript variables ``popupWaitHtml`` and ``popupNoFilesHtml``
- Unused template ``irods_info.html``
- Unused list view and template from example users app
