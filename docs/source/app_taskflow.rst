.. _app_taskflow:


Taskflow Backend
^^^^^^^^^^^^^^^^

The ``taskflowbackend`` backend app is an optional add-on used if your site
setup contains the separate **SODAR Taskflow** data transaction service.

If you have not set up a SODAR Taskflow service for any purpose, this backend
is not needed and can be ignored.


Basics
======

The ``taskflowbackend`` backend app is used in the main SODAR site to
communicate with an external SODAR Taskflow service to manage large-scale data
transactions. It has no views or database models and only provides an API for
other apps to use.

.. note::

    At the time of writing, SODAR Taskflow is in development and has not been
    made public.


Installation
============

.. warning::

    To install this app you **must** have the ``django-sodar-core`` package
    installed and the ``projectroles`` app integrated into your Django site.
    See the :ref:`projectroles integration document <app_projectroles_integration>`
    for instructions.

Django Settings
---------------

The taskflowbackend app is available for your Django site after installing
``django-sodar-core``. Add the app into ``THIRD_PARTY_APPS`` as follows:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'taskflowbackend.apps.TaskflowbackendConfig',
    ]

Next add the backend to the list of enabled backend plugins:

.. code-block:: python

    ENABLED_BACKEND_PLUGINS = env.list('ENABLED_BACKEND_PLUGINS', None, [
        # ...
        'taskflow',
    ])

The following app settings **must** be included in order to use the backend.
Note that the values for ``TASKFLOW_TARGETS`` depend on your SODAR Taskflow
configuration.

.. code-block:: python

    # Taskflow backend settings
    TASKFLOW_BACKEND_HOST = env.str('TASKFLOW_BACKEND_HOST', 'http://0.0.0.0')
    TASKFLOW_BACKEND_PORT = env.int('TASKFLOW_BACKEND_PORT', 5005)
    TASKFLOW_SODAR_SECRET = env.str('TASKFLOW_SODAR_SECRET', 'CHANGE ME!')
    TASKFLOW_TARGETS = [
        'sodar',
        # ..
    ]

Register Plugin
---------------

To register the taskflowbackend plugin, run the following management command:

.. code-block:: console

    $ ./manage.py syncplugins

You should see the following output:

.. code-block:: console

    Registering Plugin for taskflowbackend.plugins.BackendPlugin


Usage
=====

Once enabled, Retrieve the backend API class with the following in your Django
app python code:

.. code-block:: python

    from projectroles.plugins import get_backend_api
    taskflow = get_backend_api('taskflow')

See the docstrings of the API for more details.

To initiate sync of existing data with your SODAR Taskflow service, you can use
the following management command:

.. code-block:: console

    ./manage.py synctaskflow


Django API Documentation
========================

The ``TaskflowAPI`` class contains the SODAR Taskflow backend API. It should be
initialized using the ``Projectroles.plugins.get_backend_api()`` function.

.. autoclass:: taskflowbackend.api.TaskflowAPI
    :members:
