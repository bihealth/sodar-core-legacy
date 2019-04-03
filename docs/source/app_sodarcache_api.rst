.. _app_sodarcache_api:


Sodar Cache Backend API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains API documentation for the backend plugin in the
``sodarcache`` app. Included are functionalities and classes intended to be used
by other applications.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


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
