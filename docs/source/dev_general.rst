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

App Setting API
---------------

For accessing and modifying app settings for project or site apps, you should
use the ``AppSettingAPI``. Below is an example of invoking the API. For the full
API docs, see :ref:`app_projectroles_api_django`.

.. code-block:: python

    from projectroles.app_settings import AppSettingAPI
    app_settings = AppSettingAPI()
    app_settings.get_app_setting('app_name', 'setting_name', project_object)  # Etc..

Form Base Classes
-----------------

Although not required, it is recommended to use common SODAR Core base classes
with built-in helpers for your Django forms. ``SODARForm`` and
``SODARModelForm`` extend Django's ``Form`` and ``ModelForm`` respectively.
These base classes can be imported from ``projectroles.forms``. Currently they
add logging to ``add_error()`` calls, which helps administrators track form
issues encountered by users. Further improvements are to be added in the future.

Pagination Template
-------------------

A common template for adding navigation for list pagination can be found in
``projectroles/_pagination.html``. This can be included to any Django
``ListView`` template which provides the ``paginate_by`` definition, enabling
pagination. If a smaller layout is desired, the ``pg_small`` argument can be
used. An example can be seen below:

.. code-block:: django

    {% include 'projectroles/_pagination.html' with pg_small=True %}


Testing
=======

SODAR Core provides a range of ready made testing classes and mixins for
different aspects of SODAR app testing, from user permissions to UI testing.
See ``projectroles.tests`` for different base classes.

Test Settings
-------------

SODAR Core provides settings for configuring your UI tests, if using the base
UI test classes found in ``projectroles.tests.test_ui``. Default values for
these settings can be found in ``config/settings/test.py``. The settins are as
follows:

- ``PROJECTROLES_TEST_UI_CHROME_OPTIONS``: Options for Chrome through Selenium.
  Can be used to e.g. enable/disable headless testing mode.
- ``PROJECTROLES_TEST_UI_WINDOW_SIZE``: Custom browser window size.
- ``PROJECTROLES_TEST_UI_WAIT_TIME``: Maximum wait time for UI test operations
- ``PROJECTROLES_TEST_UI_LEGACY_LOGIN``: If set ``True``, use the legacy UI
  login and redirect function for testing with different users. This can be used
  if e.g. issues with cookie-based logins are encountered.
