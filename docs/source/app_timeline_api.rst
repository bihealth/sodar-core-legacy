.. _app_timeline_api:


Timeline API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains API documentation for the ``timeline`` app. Included
are functionalities and classes intended to be used by other applications.


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
