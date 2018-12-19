.. _app_projectroles_custom:

Projectroles Customization
^^^^^^^^^^^^^^^^^^^^^^^^^^

Here you can find some customization instructions and tips for SODAR Core.

**NOTE:** When viewing this document in GitLab critical content will by default
be missing. Please click "display source" if you want to read this in GitLab.


CSS Overrides
=============

While it is strongly recommended to use the Projectroles layout and styles,
there are of course many possibilities for customization.

If some of the CSS definitions in ``{STATIC}/projectroles/css/projectroles.css``
do not suit your purposes, it is of course possible to override them in your own
includes. It is still recommended to include the *"Flexbox page setup"* section
as is.

In this chapter are examples of overrides you can place e.g. in ``project.css``
to change certain defaults.

.. hint::

    While not explicitly mentioned, some parameters may require the
    ``!important`` argument to take effect on your site.

Static Element Coloring
-----------------------

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


Title Bar
=========

You can implement your own title bar by replacing the default base.html include
of ``projectroles/_site_titlebar.html`` with your own HTML or include.

When doing this, it is possible to include elements from the default title bar
separately:

- Search form: ``projectroles/_site_titlebar_search.html``
- Site app and user operation dropdown:
  ``projectroles/_site_titlebar_dropdown.html``

See the templates themselves for further instructions.


Additional Title Bar Links
==========================

If you want to add additional links *not* related to apps in the title bar, you
can implement in the template file
``{SITE_NAME}/templates/include/_titlebar_nav.html``. This can be done for e.g.
documentation links or linking to external sites. Example:

.. code-block:: django

    {# Example extra link #}
    <li class="nav-item">
      <a href="#" class="nav-link" id="site-extra-link-x" target="_blank">
        <i class="fa fa-fw fa-question-circle"></i> Extra Link
      </a>
    </li>


Site Icon
=========

An optional site icon can be placed into ``{STATIC}/images/logo_navbar.png`` to
be displayed in the default Projectroles title bar.


Project Breadcrumb
==================

To add custom content in the end of the default project breadcrumb, use
``{% block nav_sub_project_extend %}`` in your app template.

The entire breadcrumb element can be overridden by declaring
``{% block nav_sub_project %}`` block in your app template.


Footer
======

Footer content can be specified in the optional template file
``{SITE_NAME}/templates/include/_footer.html``.
