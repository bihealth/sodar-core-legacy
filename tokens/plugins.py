from projectroles.plugins import SiteAppPluginPoint


class ProjectAppPlugin(SiteAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    name = 'token'

    title = 'API Tokens'

    #: Iconify icon
    icon = 'mdi:key-chain-variant'

    entry_point_url_id = 'tokens:list'

    description = 'API Token Management'

    #: Required permission for accessing the app
    app_permission = 'tokens.access'
