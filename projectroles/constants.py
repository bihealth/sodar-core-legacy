"""SODAR constants definition and helper functions"""


# Global SODAR constants
SODAR_CONSTANTS = {
    # Project roles
    'PROJECT_ROLE_OWNER': 'project owner',
    'PROJECT_ROLE_DELEGATE': 'project delegate',
    'PROJECT_ROLE_CONTRIBUTOR': 'project contributor',
    'PROJECT_ROLE_GUEST': 'project guest',
    # Project types
    'PROJECT_TYPE_CATEGORY': 'CATEGORY',
    'PROJECT_TYPE_PROJECT': 'PROJECT',
    # Submission status
    'SUBMIT_STATUS_OK': 'OK',
    'SUBMIT_STATUS_PENDING': 'PENDING',
    'SUBMIT_STATUS_PENDING_TASKFLOW': 'PENDING-TASKFLOW',
    # RemoteSite mode
    'SITE_MODE_SOURCE': 'SOURCE',
    'SITE_MODE_TARGET': 'TARGET',
    # RemoteProject access types
    'REMOTE_LEVEL_NONE': 'NONE',
    'REMOTE_LEVEL_VIEW_AVAIL': 'VIEW_AVAIL',
    'REMOTE_LEVEL_READ_INFO': 'READ_INFO',
    'REMOTE_LEVEL_READ_ROLES': 'READ_ROLES',
    # Choices for forms/admin with project type
    'PROJECT_TYPE_CHOICES': [('CATEGORY', 'Category'), ('PROJECT', 'Project')],
    # RemoteSite modes
    'SITE_MODES': ['SOURCE', 'TARGET'],
    # RemoteProject access type legend
    'REMOTE_ACCESS_LEVELS': {
        'NONE': 'No access',
        'VIEW_AVAIL': 'View availability',
        'READ_INFO': 'Read information',
        'READ_ROLES': 'Read members',
    },
}


def get_sodar_constants(default=False):
    """
    Return SODAR_CONSTANTS from settings if present, else from default
    definition.
    """
    if not default:
        from django.conf import settings

        if hasattr(settings, 'SODAR_CONSTANTS'):
            return settings.SODAR_CONSTANTS
    return SODAR_CONSTANTS
