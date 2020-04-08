.. _glossary:


Glossary
^^^^^^^^

.. glossary::

    App Plugin
        Mechanism for defining common properties and operations for dynamically
        including content and functionality from apps in SODAR Core views.

    App Settings
        Project or user specific settings defined in SODAR Core app plugins.
        Different from e.g. Django settings used to configure the web site.

    Backend App
        SODAR Core application which is used to provide additional functionality
        to other SODAR Core apps. Does not have its own GUI entry point. Common
        use cases include APIs to external services or other apps.

    Backend API
        Django API provided by a backend app, to be dynamically imported and
        used by other SODAR Core based Django apps.

    Django API
        Application programming interface offered by an app, to be used by other
        apps within the Django site.

    Django App
        Application built for the Django web framework, including (but not
        limited to) SODAR Core based apps.

    Django Settings
        Django settings used to configure the website. SODAR Core
        apps also use Django settings for configuring framework and app
        behaviour.

    Django Site
        Web site built on the Django framework, including (but not limited to)
        any website based on SODAR Core.

    Peer Site
        A SODAR Core based web site which mirrors one or more projects also
        mirrored on the currrently active site. This allows linking to remote
        projects on other sites where the user would have access.

    Project App
        SODAR Core application with the scope of providing data and
        functionality related to a specific project. Uses project-based access
        control.

    SODAR
        System for Omics Data Access and Retrieval. An omics research data
        management system which is the origin of the reusable SODAR Core
        framework.

    SODAR Core
        Core framework and reusable apps originally built for the SODAR project.

    SODAR Core App
        Django application with additional SODAR Core features. This includes
        one or more app plugin definitions to enable dynamic inclusion of the
        app into the SODAR Core framework, as well as project access control for
        project apps.

    SODAR Core Based Site
        Django-based web site using SODAR Core apps as its framework.

    Site App
        SODAR Core application with does not limit its scope to a single
        project. Common use cases include user account management and
        administrative tools.

    Source Site
        SODAR Core based web site which mirrors project metadata and access
        control to "target" sites.

    Target Site
        SODAR Core based web site which mirrors project metadata and access
        control from a "source" site.
