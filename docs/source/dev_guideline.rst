.. _dev_guideline:

General Guidelines
^^^^^^^^^^^^^^^^^^

Below you can find general development guidelines for putting together your
SODAR Core based site.

- Best practices from `Two Scoops <https://www.twoscoopspress.com/>`_
  should be followed where applicable.
- To maintain consistency, app packages should be named without delimiting
  characters, e.g. ``projectroles`` and ``userprofile``.
- It is recommended to add a *"Projectroles dependency"* comment when directly
  importing e.g. mixins or tags from the ``projectroles`` app.
- Hard-coded imports from apps *other than* ``projectroles`` should in most
  cases be avoided. Instead of hard imports, you should use the plugin
  structure. This helps maintain the possibility to dynamically include or
  exclude applications. See the ``example_backend_app`` for an example.
- Using Bootstrap 4 classes together with SODAR specific overrides and
  extensions provided in ``projectroles.js`` is recommended. A full layout style
  guide will be provided in the future.
- It is strongly recommended to pin your site's dependencies, including the
  ``django-sodar-core`` package, to a specific version number. Breaking changes
  may occur unexpectedly in projects of this scale and pulling latest versions
  of dependencies upon e.g. deployment may result in unexpected behaviour or
  errors.
