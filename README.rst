SODAR Core
^^^^^^^^^^

SODAR (System for Omics Data Access and Retrieval) is a specialized system for
managing data in omics research projects.

The SODAR Core repository containes reusable and non-domain-specific apps making
up the base of the SODAR system. These apps can be used for any Django
application which wants to make use of the following features:

- Project-based user access control
- Dynamic app content management
- Advanced project activity logging

This repository provides the following installable Django apps:

- **projectroles**: Base app for project access management and
  dynamic app content management. All other apps require the integration of
  projectroles.
- **timeline**: Project app for logging and viewing project-related activity.
- **userprofile**: Site app for viewing user profiles.

Also included are resources and examples for developing SODAR compatible apps.

See ``docs`` for detailed documentation on use, integration and development.

:License: MIT
