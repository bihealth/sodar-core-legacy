.. _app_sodarcache_api_django:


Sodarcache Backend API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains Django API documentation for the backend plugin in the
``sodarcache`` app. Included are functionalities and classes intended to be used
by other applications.


Backend API
===========

The ``SodarCacheAPI`` class contains the Sodar Cache backend API. It should be
initialized with ``Projectroles.plugins.get_backend_api('sodar_cache')``.

.. autoclass:: sodarcache.api.SodarCacheAPI
    :members:


Models
======

.. automodule:: sodarcache.models
    :members:
