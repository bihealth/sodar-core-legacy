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


Fixed
-----

- Tests referring to the ``filesfolders`` app not included in this project
- ``TestHomeView.test_render()`` assumed extra SODAR system user was present (see omics_data_mgmt#367)
