import logging

from django.contrib import auth
from django.core.management.base import BaseCommand
from django.db import transaction

from projectroles.utils import set_user_group


User = auth.get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronizes user groups based on user name'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        logger.info('Synchronizing user groups..')

        with transaction.atomic():
            for user in User.objects.all():
                user.groups.clear()
                user.save()
                group_name = set_user_group(user)

                if group_name:
                    logger.debug(
                        'Group set: {} -> {}'.format(user.username, group_name)
                    )

        logger.info(
            'Synchronized groups for {} users'.format(
                User.objects.all().count()
            )
        )
