.. _app_sodarprojectcache_api:


Sodar Project Cache API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains API documentation for the ``sodarprojectcache`` app.
Included are functionalities and classes intended to be used by other
applications.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


Backend API
===========

The ``SodarProjectCacheAPI`` class contains the Sodar Project Cache backend API.
It should be initialized using the ``Projectroles.plugins.get_backend_api()``
function.

.. autoclass:: sodarprojectcache.api.SodarProjectCacheAPI
    :members:

Models
======

.. automodule:: sodarprojectcache.models
    :members: