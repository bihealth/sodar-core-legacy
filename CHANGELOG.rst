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
- ``SITE_TITLE`` setting
- ``example_site_app`` for demonstrating site apps

Changed
-------

- Move custom modal into ``projectroles/_modal.html``
- Check for user.name in user dropdown
- Move content block structure and sidebar inside ``projectroles/base.html``
- Move search form into optional include template ``projectroles/_search_form.html``
- Move site title bar into optional include template ``projectroles/_site_titlebar.html``
- Title bar CSS and layout tweaks
- Move ``search.js`` under projectroles

Fixed
-----

- Tests referring to the ``filesfolders`` app not included in this project
- ``TestHomeView.test_render()`` assumed extra SODAR system user was present (see omics_data_mgmt#367)
- Tour link setup placing
