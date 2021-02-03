"""Tests for email sending in the projectroles Django app"""

from django.core import mail
from django.urls import reverse

from test_plus.test import TestCase, RequestFactory

from projectroles.models import Role, SODAR_CONSTANTS
from projectroles.email import (
    send_role_change_mail,
    send_generic_mail,
    send_project_create_mail,
)
from projectroles.tests.test_models import ProjectMixin, RoleAssignmentMixin


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


# Local constants
SUBJECT_BODY = 'Test subject'
MESSAGE_BODY = 'Test message'
INVALID_EMAIL = 'ahch0La8lo0eeT8u'


class TestEmailSending(ProjectMixin, RoleAssignmentMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR
        )[0]
        self.role_guest = Role.objects.get_or_create(name=PROJECT_ROLE_GUEST)[0]

        # Init users
        self.user_owner = self.make_user('owner')
        self.user_owner.email = 'owner_user@example.com'
        self.user_owner.save()

        # Init projects
        self.category = self._make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self._make_assignment(
            self.category, self.user_owner, self.role_owner
        )

        self.project = self._make_project(
            'sub_project', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self._make_assignment(
            self.project, self.user_owner, self.role_owner
        )

    def test_role_create_mail(self):
        """Test role creation mail sending"""
        with self.login(self.user_owner):
            request = self.factory.get(reverse('home'))
            request.user = self.user_owner
            email_sent = send_role_change_mail(
                change_type='create',
                project=self.owner_as.project,
                user=self.owner_as.user,
                role=self.owner_as.role,
                request=request,
            )
            self.assertEqual(email_sent, 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_role_update_mail(self):
        """Test role updating mail sending"""
        with self.login(self.user_owner):
            request = self.factory.get(reverse('home'))
            request.user = self.user_owner
            email_sent = send_role_change_mail(
                change_type='update',
                project=self.owner_as.project,
                user=self.owner_as.user,
                role=self.owner_as.role,
                request=request,
            )
            self.assertEqual(email_sent, 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_role_delete_mail(self):
        """Test role deletion mail sending"""
        with self.login(self.user_owner):
            request = self.factory.get(reverse('home'))
            request.user = self.user_owner
            email_sent = send_role_change_mail(
                change_type='delete',
                project=self.owner_as.project,
                user=self.owner_as.user,
                role=None,
                request=request,
            )
            self.assertEqual(email_sent, 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_project_create_mail(self):
        """Test project creation mail sending"""
        new_project = self._make_project(
            'New Project', PROJECT_TYPE_PROJECT, self.category
        )
        new_user = self.make_user('new_user')
        new_user.email = 'new_user@example.com'
        new_user.save()
        self._make_assignment(new_project, new_user, self.role_owner)

        with self.login(new_user):
            request = self.factory.get(reverse('home'))
            request.user = new_user
            email_sent = send_project_create_mail(
                project=new_project,
                request=request,
            )
            self.assertEqual(email_sent, 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].reply_to[0], new_user.email)

    def test_generic_mail_user(self):
        """Test send_generic_mail() with a User recipient"""
        with self.login(self.user_owner):
            request = self.factory.get(reverse('home'))
            request.user = self.user_owner
            email_sent = send_generic_mail(
                subject_body=SUBJECT_BODY,
                message_body=MESSAGE_BODY,
                recipient_list=[self.user_owner],
                request=request,
                reply_to=[self.user_owner.email],
            )
            self.assertEqual(email_sent, 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_generic_mail_str(self):
        """Test send_generic_mail() with an email string recipient"""
        with self.login(self.user_owner):
            request = self.factory.get(reverse('home'))
            request.user = self.user_owner
            email_sent = send_generic_mail(
                subject_body=SUBJECT_BODY,
                message_body=MESSAGE_BODY,
                recipient_list=[self.user_owner.email],
                request=request,
                reply_to=[self.user_owner.email],
            )
            self.assertEqual(email_sent, 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].reply_to[0], self.user_owner.email)

    def test_generic_mail_multiple(self):
        """Test send_generic_mail() with multiple recipients"""

        # Init new user
        user_new = self.make_user('newuser')

        with self.login(self.user_owner):
            request = self.factory.get(reverse('home'))
            request.user = self.user_owner
            email_sent = send_generic_mail(
                subject_body=SUBJECT_BODY,
                message_body=MESSAGE_BODY,
                recipient_list=[self.user_owner, user_new],
                request=request,
            )
            self.assertEqual(email_sent, 2)
            self.assertEqual(len(mail.outbox), 2)
