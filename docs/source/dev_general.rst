.. _dev_general:


General Development Guidelines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Python code should comply with PEP8
- Please follow the best practices of `Two Scoops <https://www.twoscoopspress.com/>`_
  where applicable
- App packages should be named without delimiting characters, e.g.
  ``projectroles`` and ``userprofile``
- It is recommended to add a *"Projectroles dependency"* comment when directly
  importing e.g. mixins or tags from the ``projectroles`` app
- Hard-coded imports from apps *other than* ``projectroles`` should be avoided
    - Use the plugin structure instead
    - See the ``example_backend_app`` for an example


