SODAR Core
^^^^^^^^^^

SODAR (System for Omics Data Access and Retrieval) is a specialized system for
managing data in omics research projects.

The SODAR Core repository containes reusable and non-domain-specific apps making
up the base of the SODAR system. These apps can be used for any Django
application which wants to make use of the following features:

- Project-based user access control
- Dynamic app content management
- Advanced project activity logging *(coming soon)*

This repository provides the following installable Django apps:

- **projectroles**: The required base app for project access management and
  dynamic project content inclusion
- **userprofile**: User profile app (requires projectroles)

Also included are resources and examples for developing SODAR compatible apps.

See ``docs`` for detailed documentation on use, integration and development.

:License: MIT
