.. _app_timeline:


Timeline App
^^^^^^^^^^^^

The ``timeline`` app enables the developer of a SODAR Core based site to log
project related user events and link objects (both existing and deleted) to
those events.

Unlike the standard Django object history accessible in the admin
site, these events are not restricted to creation/modification of objects in the
Django database, but can concern any user-triggered activity.

The events can also have multiple temporal status states in case of e.g. events
requiring async requests.

The app provides front-end views to list timeline events for projects,
categories and objects. Also included is a backend API for saving desired
activity as timeline events. For details on how to use these, see the
:ref:`timeline usage documentation <app_timeline_usage>`.

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   Installation <app_timeline_install>
   Usage <app_timeline_usage>
   Django API Documentation <app_timeline_api_django>
