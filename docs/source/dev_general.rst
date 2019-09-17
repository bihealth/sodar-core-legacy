.. _dev_general:


General Development Topics
^^^^^^^^^^^^^^^^^^^^^^^^^^


Guidelines
==========

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


Common Helpers
==============

Via the projectroles app, SODAR Core provides optional templates for aiding in
maintaining common functionality and layout. Those are defined here.

Pagination Template
-------------------

A common template for adding navigation for list pagination can be found in
``projectroles/_pagination.html``. This can be included to any Django
``ListView`` template which provides the ``paginate_by`` definition, enabling
pagination. If a smaller layout is desired, the ``pg_small`` argument can be
used. An example can be seen below:

.. code-block:: django

    {% include 'projectroles/_pagination.html' with pg_small=True %}
