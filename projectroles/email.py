"""Email creation and sending for the projectroles app"""

import logging
import re

from django.conf import settings
from django.contrib import auth, messages
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.timezone import localtime

from projectroles.app_settings import AppSettingAPI
from projectroles.utils import build_invite_url, get_display_name


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)
User = auth.get_user_model()


# Settings
SUBJECT_PREFIX = settings.EMAIL_SUBJECT_PREFIX.strip() + ' '
EMAIL_SENDER = settings.EMAIL_SENDER
DEBUG = settings.DEBUG
SITE_TITLE = settings.SITE_INSTANCE_TITLE
ADMIN_RECIPIENT = settings.ADMINS[0]

# Local constants
EMAIL_RE = re.compile(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')


# Generic Elements -------------------------------------------------------------


MESSAGE_HEADER = r'''
Dear {recipient},

This email has been automatically sent to you by {site_title}.

'''.lstrip()

MESSAGE_HEADER_NO_RECIPIENT = r'''
This email has been automatically sent to you by {site_title}.
'''.lstrip()

NO_REPLY_NOTE = r'''
Please do not reply to this email.
'''

MESSAGE_FOOTER = r'''

For support and reporting issues regarding {site_title},
contact {admin_name} ({admin_email}).
'''


# Role Change Template ---------------------------------------------------------


SUBJECT_ROLE_CREATE = 'Membership granted for {project_label} "{project}"'
SUBJECT_ROLE_UPDATE = 'Membership changed in {project_label} "{project}"'
SUBJECT_ROLE_DELETE = 'Membership removed from {project_label} "{project}"'

MESSAGE_ROLE_CREATE = r'''
{issuer} has granted you the membership
in {project_label} "{project}" with the role of "{role}".

To access the {project_label} in {site_title}, please click on
the following link:
{project_url}
'''.lstrip()

MESSAGE_ROLE_UPDATE = r'''
{issuer} has changed your membership
role in {project_label} "{project}" into "{role}".

To access the {project_label} in {site_title}, please click on
the following link:
{project_url}
'''.lstrip()

MESSAGE_ROLE_DELETE = r'''
{issuer} has removed your membership from {project_label} "{project}".
'''.lstrip()


# Invite Template --------------------------------------------------------------


SUBJECT_INVITE = 'Invitation for {project_label} "{project}"'

MESSAGE_INVITE_BODY = r'''
You have been invited by {issuer}
to share data in the {project_label} "{project}" with the
role of "{role}".

To accept the invitation and access the {project_label} in {site_title},
please click on the following link:
{invite_url}

Please note that the link is only to be used once. After successfully
accepting the invitation, please access the project with its URL or
through the project list on the site's "Home" page.

This invitation will expire on {date_expire}.
'''

MESSAGE_INVITE_ISSUER = r'''
Message from the sender of this invitation:
----------------------------------------
{}
----------------------------------------
'''


# Invite Acceptance Notification Template --------------------------------------


SUBJECT_ACCEPT = 'Invitation accepted by {user} for {project_label} "{project}"'

MESSAGE_ACCEPT_BODY = r'''
Invitation sent by you for role of "{role}" in {project_label} "{project}"
has been accepted by {user}.
They have been granted access in the {project_label} accordingly.
'''.lstrip()


# Invite Expiry Notification Template ------------------------------------------


SUBJECT_EXPIRY = 'Expired invitation used by {user_name} in "{project}"'

MESSAGE_EXPIRY_BODY = r'''
Invitation sent by you for role of "{role}" in {project_label} "{project}"
was attempted to be used by {user_name} ({user_email}).

This invitation has expired on {date_expire}. Because of this,
access was not granted to the user.

Please add the role manually with "Add Member", if you still wish
to grant the user access to the {project_label}.
'''.lstrip()


# Project/Category Creation Notification Template ------------------------------


SUBJECT_PROJECT_CREATE = '{project_type} "{project}" created by {user}'

MESSAGE_PROJECT_CREATE_BODY = r'''
{user} has created a new {project_type}
under "{category}".
You are receiving this email because you are the owner of the parent category.
You have automatically inherited owner rights to the created {project_type}.

Title: {project}
Owner: {owner}

You can access the project at the following link:
{project_url}
'''.lstrip()


# Project/Category Moving Notification Template ------------------------------


SUBJECT_PROJECT_MOVE = '{project_type} "{project}" moved by {user}'

MESSAGE_PROJECT_MOVE_BODY = r'''
{user} has moved the {project_type} "{project}"
under "{category}".
You are receiving this email because you are the owner of the parent category.
You have automatically inherited owner rights to the created {project_type}.

Title: {project}
Owner: {owner}

You can access the project at the following link:
{project_url}
'''.lstrip()


# Email composing helpers ------------------------------------------------------


def get_email_user(user):
    """
    Return a string representation of a user object for emails.

    :param user: SODARUser object
    :return: string
    """
    ret = user.get_full_name()
    if user.email:
        ret += ' ({})'.format(user.email)
    return ret


def get_invite_body(project, issuer, role_name, invite_url, date_expire_str):
    """
    Return the invite content header.

    :param project: Project object
    :param issuer: User object
    :param role_name: Display name of the Role object
    :param invite_url: Generated URL for the invite
    :param date_expire_str: Expiry date as a pre-formatted string
    :return: string
    """
    body = MESSAGE_HEADER_NO_RECIPIENT.format(site_title=SITE_TITLE)
    body += MESSAGE_INVITE_BODY.format(
        issuer=get_email_user(issuer),
        project=project.title,
        role=role_name,
        invite_url=invite_url,
        date_expire=date_expire_str,
        site_title=SITE_TITLE,
        project_label=get_display_name(project.type),
    )
    if not issuer.email and not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
        body += NO_REPLY_NOTE
    return body


def get_invite_message(message=None):
    """
    Return the message from invite issuer, of empty string if not set.

    :param message: Optional user message as string
    :return: string
    """
    if message and len(message) > 0:
        return MESSAGE_INVITE_ISSUER.format(message)
    return ''


def get_email_header(header):
    """
    Return the email header.

    :return: string
    """
    return getattr(settings, 'PROJECTROLES_EMAIL_HEADER', None) or header


def get_email_footer():
    """
    Return the email footer.

    :return: string
    """
    custom_footer = getattr(settings, 'PROJECTROLES_EMAIL_FOOTER', None)
    if custom_footer:
        return '\n' + custom_footer
    return MESSAGE_FOOTER.format(
        site_title=SITE_TITLE,
        admin_name=ADMIN_RECIPIENT[0],
        admin_email=ADMIN_RECIPIENT[1],
    )


def get_invite_subject(project):
    """
    Return invite email subject.

    :param project: Project object
    :return: string
    """
    return SUBJECT_PREFIX + SUBJECT_INVITE.format(
        project=project.title, project_label=get_display_name(project.type)
    )


def get_role_change_subject(change_type, project):
    """
    Return role change email subject.

    :param change_type: Change type ('create', 'update', 'delete')
    :param project: Project object
    :return: String
    """
    subject = SUBJECT_PREFIX
    subject_kwargs = {
        'project': project.title,
        'project_label': get_display_name(project.type),
    }
    if change_type == 'create':
        subject += SUBJECT_ROLE_CREATE.format(**subject_kwargs)
    elif change_type == 'update':
        subject += SUBJECT_ROLE_UPDATE.format(**subject_kwargs)
    elif change_type == 'delete':
        subject += SUBJECT_ROLE_DELETE.format(**subject_kwargs)
    return subject


def get_role_change_body(
    change_type, project, user_name, role_name, issuer, project_url
):
    """
    Return role change email body.

    :param change_type: Change type ('create', 'update', 'delete')
    :param project: Project object
    :param user_name: Name of target user
    :param role_name: Name of role as string
    :param issuer: User object for issuing user
    :param project_url: URL for the project
    :return: String
    """
    body = get_email_header(
        MESSAGE_HEADER.format(recipient=user_name, site_title=SITE_TITLE)
    )

    if change_type == 'create':
        body += MESSAGE_ROLE_CREATE.format(
            issuer=get_email_user(issuer),
            role=role_name,
            project=project.title,
            project_url=project_url,
            site_title=SITE_TITLE,
            project_label=get_display_name(project.type),
        )

    elif change_type == 'update':
        body += MESSAGE_ROLE_UPDATE.format(
            issuer=get_email_user(issuer),
            role=role_name,
            project=project.title,
            project_url=project_url,
            site_title=SITE_TITLE,
            project_label=get_display_name(project.type),
        )

    elif change_type == 'delete':
        body += MESSAGE_ROLE_DELETE.format(
            issuer=get_email_user(issuer),
            project=project.title,
            project_label=get_display_name(project.type),
        )

    if not issuer.email and not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
        body += NO_REPLY_NOTE
    body += get_email_footer()
    return body


def get_user_addr(user):
    """
    Return all the email addresses for a user as a list. Emails set with
    user_email_additional are included. If a user has no main email set but
    additional emails exist, the latter are returned.

    :param user: User object
    :return: list
    """

    def _validate(user, email):
        if re.match(EMAIL_RE, email):
            return True
        logger.error(
            'Invalid email for user {}: {}'.format(user.username, email)
        )

    ret = []
    if user.email and _validate(user, user.email):
        ret.append(user.email)
    add_email = app_settings.get_app_setting(
        'projectroles', 'user_email_additional', user=user
    )
    if add_email:
        for e in add_email.strip().split(';'):
            if _validate(user, e):
                ret.append(e)
    return ret


def send_mail(subject, message, recipient_list, request, reply_to=None):
    """
    Wrapper for send_mail() with logging and error messaging.

    :param subject: Message subject (string)
    :param message: Message body (string)
    :param recipient_list: Recipients of email (list)
    :param request: Request object
    :param reply_to: List of emails for the "reply-to" header (optional)
    :return: Amount of sent email (int)
    """
    try:
        e = EmailMessage(
            subject=subject,
            body=message,
            from_email=EMAIL_SENDER,
            to=recipient_list,
            reply_to=reply_to if isinstance(reply_to, list) else [],
        )
        ret = e.send(fail_silently=False)
        logger.debug(
            '{} email{} sent to {}'.format(
                ret, 's' if ret != 1 else '', ', '.join(recipient_list)
            )
        )
        return ret

    except Exception as ex:
        error_msg = 'Error sending email: {}'.format(str(ex))
        logger.error(error_msg)
        if DEBUG:
            raise ex
        messages.error(request, error_msg)
        return 0


# Sending functions ------------------------------------------------------------


def send_role_change_mail(change_type, project, user, role, request):
    """
    Send email to user when their role in a project has been changed.

    :param change_type: Change type ('create', 'update', 'delete')
    :param project: Project object
    :param user: User object
    :param role: Role object (can be None for deletion)
    :param request: HTTP request
    :return: Amount of sent email (int)
    """
    project_url = request.build_absolute_uri(
        reverse('projectroles:detail', kwargs={'project': project.sodar_uuid})
    )
    subject = get_role_change_subject(change_type, project)
    message = get_role_change_body(
        change_type=change_type,
        project=project,
        user_name=user.get_full_name(),
        role_name=role.name if role else '',
        issuer=request.user,
        project_url=project_url,
    )
    issuer_emails = get_user_addr(request.user)
    return send_mail(
        subject, message, get_user_addr(user), request, issuer_emails
    )


def send_invite_mail(invite, request):
    """
    Send an email invitation to user not yet registered in the system.

    :param invite: ProjectInvite object
    :param request: HTTP request
    :return: Amount of sent email (int)
    """
    invite_url = build_invite_url(invite, request)
    message = get_invite_body(
        project=invite.project,
        issuer=invite.issuer,
        role_name=invite.role.name,
        invite_url=invite_url,
        date_expire_str=localtime(invite.date_expire).strftime(
            '%Y-%m-%d %H:%M'
        ),
    )
    message += get_invite_message(invite.message)
    message += get_email_footer()
    subject = get_invite_subject(invite.project)
    issuer_emails = get_user_addr(invite.issuer)
    return send_mail(subject, message, [invite.email], request, issuer_emails)


def send_accept_note(invite, request, user):
    """
    Send a notification email to the issuer of an invitation when a user
    accepts the invitation.

    :param invite: ProjectInvite object
    :param request: HTTP request
    :return: Amount of sent email (int)
    """
    subject = SUBJECT_PREFIX + SUBJECT_ACCEPT.format(
        user=get_email_user(user),
        project_label=get_display_name(invite.project.type),
        project=invite.project.title,
    )
    message = get_email_header(
        MESSAGE_HEADER.format(
            recipient=invite.issuer.get_full_name(), site_title=SITE_TITLE
        )
    )
    message += MESSAGE_ACCEPT_BODY.format(
        role=invite.role.name,
        project=invite.project.title,
        user=get_email_user(user),
        site_title=SITE_TITLE,
        project_label=get_display_name(invite.project.type),
    )

    if not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
        message += NO_REPLY_NOTE
    message += get_email_footer()
    return send_mail(subject, message, get_user_addr(invite.issuer), request)


def send_expiry_note(invite, request, user_name):
    """
    Send a notification email to the issuer of an invitation when a user
    attempts to accept an expired invitation.

    :param invite: ProjectInvite object
    :param request: HTTP request
    :param user_name: User name of invited user
    :return: Amount of sent email (int)
    """
    subject = SUBJECT_PREFIX + SUBJECT_EXPIRY.format(
        user_name=user_name, project=invite.project.title
    )
    message = get_email_header(
        MESSAGE_HEADER.format(
            recipient=invite.issuer.get_full_name(), site_title=SITE_TITLE
        )
    )
    message += MESSAGE_EXPIRY_BODY.format(
        role=invite.role.name,
        project=invite.project.title,
        user_name=user_name,
        user_email=invite.email,
        date_expire=localtime(invite.date_expire).strftime('%Y-%m-%d %H:%M'),
        site_title=SITE_TITLE,
        project_label=get_display_name(invite.project.type),
    )

    if not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
        message += NO_REPLY_NOTE
    message += get_email_footer()
    return send_mail(subject, message, get_user_addr(invite.issuer), request)


def send_project_create_mail(project, request):
    """
    Send email about project creation to the owner of the parent category, if
    they are a different user than the project creator.

    :param project: Project object for the newly created project
    :param request: Request object
    :return: Amount of sent email (int)
    """
    parent = project.parent
    parent_owner = project.parent.get_owner() if project.parent else None
    project_owner = project.get_owner()
    if not parent or not parent_owner or parent_owner.user == request.user:
        return 0

    subject = SUBJECT_PROJECT_CREATE.format(
        project_type=get_display_name(project.type, title=True),
        project=project.title,
        user=get_email_user(request.user),
    )
    message = get_email_header(
        MESSAGE_HEADER.format(
            recipient=parent_owner.user.get_full_name(), site_title=SITE_TITLE
        )
    )
    message += MESSAGE_PROJECT_CREATE_BODY.format(
        user=get_email_user(request.user),
        project_type=get_display_name(project.type),
        category=parent.title,
        project=project.title,
        owner=get_email_user(project_owner.user),
        project_url=request.build_absolute_uri(
            reverse(
                'projectroles:detail', kwargs={'project': project.sodar_uuid}
            )
        ),
    )
    message += get_email_footer()
    return send_mail(
        subject,
        message,
        get_user_addr(parent_owner.user),
        request,
        reply_to=get_user_addr(request.user),
    )


def send_project_move_mail(project, request):
    """
    Send email about project being moved to the owner of the parent category, if
    they are a different user than the project creator.

    :param project: Project object for the newly created project
    :param request: Request object
    :return: Amount of sent email (int)
    """
    parent = project.parent
    parent_owner = project.parent.get_owner() if project.parent else None
    project_owner = project.get_owner()
    if not parent or not parent_owner or parent_owner.user == request.user:
        return 0

    subject = SUBJECT_PROJECT_MOVE.format(
        project_type=get_display_name(project.type, title=True),
        project=project.title,
        user=get_email_user(request.user),
    )
    message = get_email_header(
        MESSAGE_HEADER.format(
            recipient=parent_owner.user.get_full_name(), site_title=SITE_TITLE
        )
    )
    message += MESSAGE_PROJECT_MOVE_BODY.format(
        user=get_email_user(request.user),
        project_type=get_display_name(project.type),
        category=parent.title,
        project=project.title,
        owner=get_email_user(project_owner.user),
        project_url=request.build_absolute_uri(
            reverse(
                'projectroles:detail', kwargs={'project': project.sodar_uuid}
            )
        ),
    )
    message += get_email_footer()
    return send_mail(
        subject,
        message,
        get_user_addr(parent_owner.user),
        request,
        reply_to=get_user_addr(request.user),
    )


def send_generic_mail(
    subject_body, message_body, recipient_list, request, reply_to=None
):
    """
    Send a notification email to the issuer of an invitation when a user
    attempts to accept an expired invitation.

    :param subject_body: Subject body without prefix (string)
    :param message_body: Message body before header or footer (string)
    :param recipient_list: Recipients (list of User objects or email strings)
    :param reply_to: List of emails for the "reply-to" header (optional)
    :param request: HTTP request
    :return: Amount of mail sent (int)
    """
    subject = SUBJECT_PREFIX + subject_body
    ret = 0

    for recipient in recipient_list:
        if isinstance(recipient, User):
            recp_name = recipient.get_full_name()
            recp_addr = get_user_addr(recipient)
        else:
            recp_name = 'recipient'
            recp_addr = [recipient]

        message = get_email_header(
            MESSAGE_HEADER.format(recipient=recp_name, site_title=SITE_TITLE)
        )
        message += message_body
        if not reply_to and not settings.PROJECTROLES_EMAIL_SENDER_REPLY:
            message += NO_REPLY_NOTE
        message += get_email_footer()
        ret += send_mail(subject, message, recp_addr, request, reply_to)

    return ret
