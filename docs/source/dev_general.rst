.. _dev_general:


General Development Guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Best practices from `Two Scoops <https://www.twoscoopspress.com/>`_
  should be followed where applicable
- To maintain consistency, app packages should be named without delimiting
  characters, e.g. ``projectroles`` and ``userprofile``
- It is recommended to add a *"Projectroles dependency"* comment when directly
  importing e.g. mixins or tags from the ``projectroles`` app
- Hard-coded imports from apps *other than* ``projectroles`` should be avoided
    - Use the plugin structure instead
    - See the ``example_backend_app`` for an example
- Using Bootstrap 4 classes together with SODAR specific overrides and
  extensions provided in ``projectroles.js`` is recommended
