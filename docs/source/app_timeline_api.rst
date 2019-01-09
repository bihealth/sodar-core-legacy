.. _app_timeline_api:


Timeline API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains API documentation for the ``timeline`` app. Included
are functionalities and classes intended to be used by other applications.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


Backend API
===========

The ``TimelineAPI`` class contains the Timeline backend API. It should be
initialized using the ``Projectroles.plugins.get_backend_api()`` function.

.. autoclass:: timeline.api.TimelineAPI
    :members:

Models
======

.. automodule:: timeline.models
    :members:
