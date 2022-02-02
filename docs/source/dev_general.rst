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

Management Command Logger
-------------------------

When developing management commands for your apps, you may want to log certain
events while also ensuring relevant output is provided to the administrator
issuing a command. For this SODAR Core provides the
``ManagementCommandLogger`` class. It can be called like the standard Python
logger with shortcut commands such as ``info()``, ``debug()`` etc. If you need
to access the actual Python logger being used, you can access it via
``ManagementCommandLogger.logger``. Example of logger usage can be seen below.

.. code-block:: python

    from projectroles.management.logging import ManagementCommandLogger
    logger = ManagementCommandLogger(__name__)
    logger.info('Testing')

.. note::

    The use of this logger class assumes your site sets up logging simlarly to
    the example site and the SODAR Django Site template, including the use of a
    ``LOGGING_LEVEL`` Django settings variable.

.. hint::

    To disable redundant console output from commands using this logger in e.g.
    your site's test configuration, you can set the
    ``LOGGING_DISABLE_CMD_OUTPUT`` Django setting to ``True``.


Using Icons
===========

To use icons in your apps, use the ``iconify`` class along with the collection
and icon name into the ``data-icon`` attribute. See
`Iconify <https://docs.iconify.design/implementations/css.html>`_ and
`django-iconify <https://edugit.org/AlekSIS/libs/django-iconify/-/blob/master/README.rst>`_
documentation for further information.

Example:

.. code-block:: HTML

    <i class="iconify" data-icon="mdi:home"></i>

Also make sure to modify the ``icon`` attribute of your app plugins to include
the full ``collection:name`` syntax for Iconify icons.

In certain client side Javascript implementations in which icons are loaded or
replaced dynamically, you may have to refer to these URLs as a direct ``img``
element:

.. code-block:: HTML

    <img src="/icons/mdi/home.svg" />

For modifiers such as color and size when using ``img`` tags,
`see here <https://docs.iconify.design/implementations/css.html>`_.


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

Base Test Classes and Helpers
-----------------------------

For base classes and mixins with useful helpers, see the ``projectroles.tests``
modules. The test cases also provide useful examples on how to set up your own
tests.

.. note::

    For REST API testing, SODAR Core uses separate base test classes for the
    internal SODAR Core API, and the API views implemented in the actual site
    built on SODAR Core. For the API views in your site, make sure to test them
    using e.g. ``TestAPIViewsBase`` and **not** ``TestCoreAPIViewsBase``.


Debugging
=========

Debugging helpers and tips are detailed in this section.

Profiling Middleware
--------------------

SODAR Core provides a cProfile using profiler for tracing back sources of page
loading slowdowns. To enable the profiler middleware, include
``projectroles.middleware.ProfilerMiddleware`` in ``MIDDLEWARE`` under your site
configuration. It is recommended to use a settings variable for this similar to
the example site configuration, where ``PROJECTROLES_ENABLE_PROFILING`` controls
this.

Once enabled, adding the ``?prof`` query string attribute to and URL displays
the profiling information.
