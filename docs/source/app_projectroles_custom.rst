.. _app_projectroles_custom:

Projectroles Customization Tips
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here you can find some customization tips for SODAR and Projectroles.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


CSS Overrides
=============

Here are some overrides you can place e.g. in ``project.css`` to change certain
defaults.

.. hint::

    While not explicitly mentioned, some parameters may require the
    ``!important`` argument to take effect on your site.

Static Element Coloring
------------------------

If you wish to recolor the background of the static elements on the page
(title bar, side bar and project navigation breadcrumb), add the following
CSS overrides.

.. code-block:: css

    .sodar-base-navbar {
      background-color: #ff00ff;
    }

    .sodar-pr-sidebar {
      background-color: #ff00ff;
    }

    .sodar-pr-sidebar-nav {
      background-color: #ff00ff;
    }

    .sodar-pr-navbar {
      background-color: #00ff00;
    }

Sidebar Width
-------------

If the sidebar is not wide enough for your liking or e.g. a name of an app
overflowing, the sidebar can be resized with the following override:

.. code-block:: css

    .sodar-pr-sidebar {
        width: 120px;
    }
