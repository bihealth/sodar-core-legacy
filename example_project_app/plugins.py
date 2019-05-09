# Projectroles dependency
from projectroles.plugins import ProjectAppPluginPoint

from .urls import urlpatterns


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (slug-safe)
    name = 'example_project_app'

    #: Title (used in templates)
    title = 'Example Project App'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    # Properties defined in ProjectAppPluginPoint -----------------------

    #: Project settings definition
    project_settings = {
        'example_setting': {
            'type': 'BOOLEAN',
            'default': False,
            'description': 'Example setting',
        }
    }

    #: FontAwesome icon ID string
    icon = 'rocket'

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = 'example_project_app:example'

    #: Description string
    description = 'This is a minimal example for a project app'

    #: Required permission for accessing the app
    app_permission = 'example_project_app.view_data'

    #: Enable or disable general search from project title bar
    search_enable = False

    #: List of search object types for the app
    search_types = []

    #: Search results template
    search_template = None

    #: App card template for the project details page
    details_template = 'example_project_app/_details_card.html'

    #: App card title for the project details page
    details_title = 'Example Project App Overview'

    #: Position in plugin ordering
    plugin_ordering = 100

    #: Example/test user settings
    user_settings = {
        'str_setting': {'type': 'STRING', 'default': ''},
        'int_setting': {'type': 'INTEGER', 'default': 0},
        'bool_setting': {
            'type': 'BOOLEAN',
            'default': False,
            'description': 'Example description',
        },
    }
