from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
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

    #: Project and user settings
    app_settings = {
        'project_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'BOOLEAN',
            'default': False,
            'description': 'Example project setting',
            'user_modifiable': True,
        },
        'project_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'JSON',
            'default': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'description': 'Example project setting for JSON. Will accept '
            'anything that json.dumps() can.',
            'user_modifiable': True,
        },
        'project_hidden_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'STRING',
            'label': 'Hidden project setting',
            'default': '',
            'description': 'Should not be displayed in forms',
            'user_modifiable': False,
        },
        'user_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'JSON',
            'label': 'Json example',
            'default': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'description': 'Example project setting for JSON. Will accept '
            'anything that json.dumps() can.',
            'user_modifiable': True,
        },
        'user_str_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'label': 'String example',
            'default': '',
            'description': 'Example user setting',
            'user_modifiable': True,
        },
        'user_int_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'INTEGER',
            'label': 'Int example',
            'default': 0,
            'user_modifiable': True,
        },
        'user_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'BOOLEAN',
            'label': 'Bool Example',
            'default': False,
            'user_modifiable': True,
        },
        'user_hidden_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'label': 'Hidden user setting',
            'default': '',
            'description': 'Should not be displayed in forms',
            'user_modifiable': False,
        },
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

    def get_statistics(self):
        return {
            'example_stat': {
                'label': 'Example Stat',
                'value': 9000,
                'description': 'Optional description goes here',
            },
            'second_example': {
                'label': 'Second Example w/ Link',
                'value': 56000,
                'url': reverse('home'),
            },
        }
