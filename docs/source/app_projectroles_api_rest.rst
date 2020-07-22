.. _app_projectroles_api_rest:


Projectroles REST API Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This document contains the HTTP REST API documentation for the ``projectroles``
app. The provided API enpoints allow project and role operations through
HTTP API calls in addition to the GUI.


API Usage
=========

Usage of the REST API is detailed in this section. These instructions also apply
to REST APIs in any other application within SODAR Core and are recommended
as guidelines for API development in your SODAR Core based Django site.

Authentication
--------------

The API supports authentication through Knox authentication tokens as well as
logging in using your SODAR username and password. Tokens are the recommended
method for security purposes.

For token access, first retrieve your token using the :ref:`app_tokens`. Add
the token in the ``Authorization`` header of your HTTP request as follows:

.. code-block:: console

    Authorization: token 90c2483172515bc8f6d52fd608e5031db3fcdc06d5a83b24bec1688f39b72bcd

Versioning
----------

The SODAR Core REST API uses accept header versioning. While specifying the
desired API version in your HTTP requests is optional, it is
**strongly recommended**. This ensures you will get the appropriate return data
and avoid running into unexpected incompatibility issues.

To enable versioning, add the ``Accept`` header to your request with the
following media type and version syntax. Replace the version number with your
expected version.

.. code-block:: console

    Accept: application/vnd.bihealth.sodar-core+json; version=0.8.2

.. note::

    The media type and version for internal SODAR Core apps are by design
    intended to be different to applications implemented in your Django site.
    Only use the aforementioned values when calling REST API views in
    projectroles or other applications installed from the django-sodar-core
    package.

Model Access and Permissions
----------------------------

Objects in SODAR Core API views are accessed through their ``sodar_uuid`` field.
This is strongly recommended for views implemented in your Django site as well,
as using a field such as ``pk`` may reveal internal database details to users as
well as be incompatible if e.g. mirroring roles between multiple SODAR Core
sites.

In the remainder of this document and other REST API documentation, *"UUID"*
refers to the ``sodar_uuid`` field of each model unless otherwise noted.

For permissions the API uses the same rules which are in effect in the SODAR Core
GUI. That means you need to have appropriate project access for each operation.

Return Data
-----------

The return data for each request will be a JSON document unless otherwise
specified.

If return data is not specified in the documentation of an API view, it will
return the appropriate HTTP status code along with an optional ``detail`` JSON
field upon a successfully processed request.

For creation views, the ``sodar_uuid`` of the created object is returned
along with other object fields.


API Views
=========

.. currentmodule:: projectroles.views_api

.. autoclass:: ProjectListAPIView

.. autoclass:: ProjectRetrieveAPIView

.. autoclass:: ProjectCreateAPIView

.. autoclass:: ProjectUpdateAPIView

.. autoclass:: RoleAssignmentCreateAPIView

.. autoclass:: RoleAssignmentUpdateAPIView

.. autoclass:: RoleAssignmentDestroyAPIView

.. autoclass:: RoleAssignmentOwnerTransferAPIView

.. autoclass:: UserListAPIView
