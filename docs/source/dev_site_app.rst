.. _dev_site_app:


Site App Development
^^^^^^^^^^^^^^^^^^^^

This document details instructions and guidelines for developing **site apps**
to be used with the SODAR Core framework.

It is recommended to read :ref:`dev_project_app` before this document.


Site App Basics
===============

Site apps are basically normal Django apps *not* hooked to SODAR projects.
However, they provide a few nice features to be used in a SODAR-enabled Django
site:

- Rules for accessing app data (similar to project apps but without the need for
  being associated with a project)
- Dynamic inclusion into the site and default templates via plugins
- The ability to show site-wide messages to users


Prerequisites
=============

See :ref:`dev_project_app`.


Models
======

No specific model implementation is required. However, it is strongly to refer
to objects using ``sodar_uuid`` fields instead of the database private key.


Rules File
==========

Generate a ``rules.py`` file similar to a project app. However, you should not
use project predicates in this one. Example:

.. code-block:: python

    import rules
    # Allow viewing data
    rules.add_perm('{APP_NAME}.view_data', rules.is_authenticated)


SiteAppPlugin
=============

Create a file ``plugins.py`` in your app's directory. In the file, declare a
``SiteAppPlugin`` class implementing
``projectroles.plugins.SiteAppPluginPoint``. Within the class, implement
member variables and functions as instructed in comments and docstrings.

.. code-block:: python

    from projectroles.plugins import SiteAppPluginPoint
    from .urls import urlpatterns

    class SiteAppPlugin(SiteAppPluginPoint):
        """Plugin for registering a site-wide app"""
        name = 'example_site_app'
        title = 'Example Site App'
        urls = urlpatterns
        # ...

The following variables and functions are **mandatory**:

- ``name``: App name (ideally should correspond to the app package name)
- ``title``: Printable app title
- ``urls``: Urlpatterns (usually imported from the app's ``urls.py`` file)
- ``icon``: Font Awesome 4.7 icon name (without the ``fa-*`` prefix)
- ``entry_point_url_id``: View ID for the app entry point
- ``description``: Verbose description of app
- ``app_permission``: Basic permission for viewing app data in project (see
  above)

Implementing the following is **optional**:

- ``app_settings``: Implement if project or user specific settings for the app
  are needed. See the plugin point definition for an example.
- ``get_messages()``: Implement if your site app needs to display site-wide
  messages for users.


Views
=====

In your views, you can still use projectroles mixins which are *not* related to
projects. Especially ``LoggedInPermissionMixin`` is useful to ensure users not
allowed to access a view are properly redirected. Example:

.. code-block:: python

    from django.views.generic import TemplateView
    from projectroles.views import LoggedInPermissionMixin

    class ExampleView(LoggedInPermissionMixin, TemplateView):
        """Site app example view"""
        permission_required = 'example_site_app.view_data'
        template_name = 'example_site_app/example.html'

.. note::

    The entry point URL is not expected to have any URL kwargs in the current
    implementation. If you intend to use a view which makes use of URL kwargs,
    you may need to modify it into also accepting a request without any
    parameters (e.g. displaying default content for the view).


Templates
=========

It is recommended for you to extend ``projectroles/base.html`` and put your
actual app content within the ``projectroles`` block. Example:

.. code-block:: django

    {# Projectroles dependency #}
    {% extends 'projectroles/base.html' %}
    {% load projectroles_common_tags %}

    {% block title %}
      Example Site App Page Title
    {% endblock title %}

    {% block projectroles %}

      <div class="container sodar-subtitle-container">
        <h2><i class="fa fa-umbrella"></i> Example Site App</h2>
      </div>

      <div class="container-fluid sodar-page-container">
        <div class="alert alert-info">
          This is an example and the entry point for <code>example_site_app</code>.
        </div>
      </div>

    {% endblock projectroles %}


Site App Messages
=================

The site app provides a way to display certain messages to users. For this, you
need to implement ``get_messages()`` in the ``SiteAppPlugin`` class.

If you need to control e.g. which user should see the message or removal of a
message after showing, you need to implement relevant logic in the function.

Example:

.. code-block:: python

    def get_messages(self, user=None):
        """
        Return a list of messages to be shown to users.
        :param user: User object (optional)
        :return: List of dicts or and empty list if no messages
        """
        return [{
            'content': 'Message content in here, can contain html',
            'color': 'info',        # Corresponds to bg-* in Bootstrap
            'dismissable': True     # False for non-dismissable
            'require_auth': True    # Only view for authorized users
        }]
