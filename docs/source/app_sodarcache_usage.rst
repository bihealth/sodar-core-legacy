.. _app_sodarcache_usage:


Sodar Cache Usage
^^^^^^^^^^^^^^^^^

Usage instructions for the ``sodarcache`` app are detailed in this document.


Backend API for Data Caching
============================

The Django backend API for caching data is located in ``sodarcache.api``. For
the full documentation, see `here <app_sodarcache_api_django>`_.

Invoking the API
----------------

The API is accessed through a backend plugin. This means you can write calls to
the API without any hard-coded imports and your code should work even if the
sodarcache app has not been installed on the site.

Initialize the API using ``projectroles.plugins.get_backend_api()`` as follows:

.. code-block:: python

    from projectroles.plugins import get_backend_api
    projectcache = get_backend_api('sodar_cache')

    if projectcache:    # Only proceed if the backend was successfully initialized
        pass

Setting and getting Cache Items
-------------------------------

Once you can access the sodarcache backend, you should set up the
``update_cache()`` function in the ``ProjectAppPlugin`` of the app with which
you want to cache or aggregate data. The update process can be limited by two
parameters: cached item name and project. If neither are specified, the function
should update cached data for all known items within all projects.

.. code-block:: python

        def update_cache(self, name=None, project=None):
        """
        Update cached data for this app, limitable to item ID and/or project.

        :param project: Project object to limit update to (optional)
        :param name: Item name to limit update to (string, optional)
        """
        # TODO: Implement this in your app plugin
        return None

Updating a specific cache item within the ``update_cache()`` function (or
elsewhere) should be done using ``sodarcache.api.set_cache_item()``. A minimal
example is as follows:

.. code-block:: python

    cache_item = projectcache.set_cache_item(
        project=project,            # Project object
        app_name=APP_NAME,          # Name of the current app
        user=request.user,          # The user triggering the cache update
        name='some_item',           # Cached item ID
        data_type='json',           # Data type ("json" currently supported)
        data={'key': 'val'},        # The actual data that should be cached
        )

.. note::

    The item ID in the ``name`` argument is not unique, but it is expected to
    be unique together with the ``project`` and ``app_name`` arguments.

Retrieve items with ``sodarcache.get_cache_item()`` or just check the
time the item was last updated with ``sodarcache.get_update_time()`` like
this:

.. code-block:: python

    projectcache.get_cache_item(
        app_name='yourapp',
        name='some_item',
        project=project,
        data_type='json'
    ) # Returns a JsonCacheItem

    projectcache.get_update_time(
        app_name='yourapp',
        name='some_item',
        project=project
    )

It is also possible to retrieve a Queryset with all cached items for a specific
project with ``sodarcache.get_project_cache()``

.. code-block:: python

    projectcache.get_project_cache(
        project=project,        # Project object
        data_type='json'        # must be 'json' for JsonCacheItem
        )

Using the Management commands
-----------------------------
To create or update the data cache for all apps and projects, you can use a
management command.

.. code-block:: console

    $ ./manage.py synccache

To limit the sync to a specific project, you can provide the ``-p`` or
``--project`` argument with the project UUID.

.. code-block:: console

    $ ./manage.py synccache -p e9701604-4ccc-426c-a67c-864c15aff6e2

Similarly, there is a command to delete all cached data:

.. code-block:: console

    $ ./manage.py deletecache



