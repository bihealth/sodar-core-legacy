import random
import string

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .constants import get_sodar_constants


# Settings
SECRET_LENGTH = getattr(settings, 'PROJECTROLES_SECRET_LENGTH', 32)
INVITE_EXPIRY_DAYS = settings.PROJECTROLES_INVITE_EXPIRY_DAYS

# SODAR constants
SODAR_CONSTANTS = get_sodar_constants()


def get_display_name(key, title=False, count=1, plural=False):
    """
    Return display name from SODAR_CONSTANTS.

    :param key: Key in SODAR_CONSTANTS['DISPLAY_NAMES'] to return (string)
    :param title: Return name in title case if true (boolean, optional)
    :param count: Item count for returning plural form, overrides plural=False
                  if not 1 (int, optional)
    :param plural: Return plural form if True, overrides count != 1 if True
                   (boolean, optional)
    :return: String
    """
    ret = SODAR_CONSTANTS['DISPLAY_NAMES'][key][
        'plural' if count != 1 or plural else 'default'
    ]
    return ret.lower() if not title else ret.title()


def get_user_display_name(user, inc_user=False):
    """
    Return full name of user for displaying.

    :param user: User object
    :param inc_user: Include user name if true (boolean)
    :return: String
    """
    if user.name != '':
        return user.name + (' (' + user.username + ')' if inc_user else '')

    # If full name can't be found, return username
    return user.username


def build_secret(length=SECRET_LENGTH):
    """
    Return secret string for e.g. public URLs.

    :param length: Length of string if specified, default value from settings
    :return: Randomized secret (string)
    """
    length = int(length) if int(length) <= 255 else 255

    return ''.join(
        random.SystemRandom().choice(string.ascii_lowercase + string.digits)
        for _ in range(length)
    )


def build_invite_url(invite, request):
    """
    Return invite URL for a project invitation.

    :param invite: ProjectInvite object
    :param request: HTTP request
    :return: URL (string)
    """
    return request.build_absolute_uri(
        reverse('projectroles:invite_accept', kwargs={'secret': invite.secret})
    )


def get_expiry_date():
    """
    Return expiry date based on current date + INVITE_EXPIRY_DAYS

    :return: DateTime object
    """
    return timezone.now() + timezone.timedelta(days=INVITE_EXPIRY_DAYS)


def get_app_names():
    """Return list of names for locally installed non-django apps"""
    ret = []

    for a in settings.INSTALLED_APPS:
        s = a.split('.')

        if s[0] not in ['django', settings.SITE_PACKAGE]:
            if len(s) > 1 and 'apps' in s:
                ret.append('.'.join(s[0 : s.index('apps')]))
            else:
                ret.append(s[0])

    return sorted(ret)
