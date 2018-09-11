SODAR Core
==========

SODAR (System for Omics Data Access and Retrieval) is a specialized project for
managing data in omics research projects.

This repository contains the core reusable and non-domain-specific apps of the
system. These apps can be used for any application which requires project-based
access and dynamic app management on a Django web site.

:License: MIT

Overview
--------

This repository provides the following installable apps to be included in a
Django site which wants to make use of SODAR compatible project and access
management:

- **projectroles**: The required base app for project access management and
  dynamic project content inclusion
- **userprofile**: User profile app (requires projectroles)

Also included are resources and examples for developing SODAR compatible apps.

See ``docs`` for detailed documentation on use, integration and development.

