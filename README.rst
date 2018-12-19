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
- Small file uploading and browsing
- Managing server-side background jobs

This repository provides the following installable Django apps:

- **projectroles**: Base app for project access management and
  dynamic app content management. All other apps require the integration of
  projectroles.
- **adminalerts**: Site app for displaying site-wide messages to all users.
- **bgjobs**: Project app for managing background jobs.
- **filesfolders**: Storage and management of small files.
- **taskflowbackend**: Backend app providing an API for the optional
  ``sodar_taskflow`` transaction service.
- **timeline**: Project app for logging and viewing project-related activity.
- **userprofile**: Site app for viewing user profiles.

Also included are resources and examples for developing SODAR compatible apps.

See ``docs`` for detailed documentation on use, integration and development.

:License: MIT
