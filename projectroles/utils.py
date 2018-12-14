import random
import string

from django.conf import settings
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

# Settings
SECRET_LENGTH = settings.PROJECTROLES_SECRET_LENGTH if \
    hasattr(settings, 'PROJECTROLES_SECRET_LENGTH') else 32
INVITE_EXPIRY_DAYS = settings.PROJECTROLES_INVITE_EXPIRY_DAYS
SYSTEM_USER_GROUP = 'system'


def get_user_display_name(user, inc_user=False):
    """
    Return full name of user for displaying
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

    return ''.join(random.SystemRandom().choice(
        string.ascii_lowercase + string.digits) for x in range(length))


def build_invite_url(invite, request):
    """
    Return invite URL for a project invitation.
    :param invite: ProjectInvite object
    :param request: HTTP request
    :return: URL (string)
    """
    return request.build_absolute_uri(reverse(
        'projectroles:invite_accept',
        kwargs={'secret': invite.secret}))


def get_expiry_date():
    """
    Return expiry date based on current date + INVITE_EXPIRY_DAYS
    :return: DateTime object
    """
    return timezone.now() + timezone.timedelta(days=INVITE_EXPIRY_DAYS)


def get_app_names():
    """Return list of names for local apps"""

    # TODO: Restrict this to SODAR Core apps
    return sorted([
        a.split('.')[0] for a in settings.INSTALLED_APPS if
        a.split('.')[0] not in ['django', settings.SITE_PACKAGE]])


def set_user_group(user):
    """Set user group based on user name"""

    if user.username.find('@') != -1:
        group_name = user.username.split('@')[1].lower()

    else:
        group_name = SYSTEM_USER_GROUP

    group, created = Group.objects.get_or_create(name=group_name)

    if group not in user.groups.all():
        group.user_set.add(user)
        return group_name
