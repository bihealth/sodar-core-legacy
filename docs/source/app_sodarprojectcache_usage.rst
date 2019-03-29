.. _app_sodarprojectcache_usage:


Sodar Project Cache Usage
^^^^^^^^^^^^^^^^^^^^^^^^^

Usage instructions for the ``sodarprojectcache`` app are detailed in this document.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


Backend API for Data Caching
============================

The API for logging events is located in ``sodarprojectcache.api``. For the full API
documentation, see `here <app_sodarprojectcache_api>`_.

Invoking the API
----------------

The API is accessed through a backend plugin. This means you can write calls to
the API without any hard-coded imports and your code should work even if the
sodarprojectcache app has not been installed on the site.

Initialize the API using ``projectroles.plugins.get_backend_api()`` as follows:

.. code-block:: python

    from projectroles.plugins import get_backend_api
    projectcache = get_backend_api('sodarprojectcache')

    if projectcache:    # Only proceed if the backend was successfully initialized
        pass

Setting and getting Cache Items
-------------------------------

Once you can access the sodarprojectcache backend, set or update a cache item
with ``sodarprojectcache.set_cache_item()``. A minimal example is as follows:

.. code-block:: python

    tl_event = projectcache.set_cache_item(
        project=project,            # Project object
        app_name=APP_NAME,          # Name of the current app
        user=request.user,          # The user triggering the cache update
        name='some_item',           # You can define these yourself, not unique
        data={'key': 'val'},        # The actual data that should be cached
        )


Retrieve items with ``sodarprojectcache.get_cache_item()`` or just check the
time the item was last updated with ``sodarprojectcache.get_update_time()`` like
this:

.. code-block:: python

    projectcache.get_cache_item(name='some_item', project=project) # returns a JsonCacheItem

    projectcache.get_update_time(name='some_item', project=project)


It is also possible to retrieve a Queryset with all cached items for a specific
project with ``sodarprojectcache.get_project_cache()``

.. code-block:: python

    projectcache.get_project_cache(
        project=project,        # Project object
        data_type='json'        # must be 'json' for JsonCacheItem
        )


Using the Management commands
-----------------------------
To update (or create) the data cache for all projects, you can use a management
command.

.. code-block:: console

    $ ./manage.py update_cache


Similarly, there is a command to delete all cached data

.. code-block:: console

    $ ./manage.py delete_cache



