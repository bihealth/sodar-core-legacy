"""
SODAR project and role management
"""

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions

default_app_config = (
    'projectroles.apps.ProjectrolesConfig'  # pylint: disable=invalid-name
)

from . import _version  # noqa

__version__ = _version.get_versions()['version']
