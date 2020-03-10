import logging

from django.contrib import auth
from django.core.management.base import BaseCommand
from django.db import transaction

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
                user.save()  # Group is updated during save

                if user.groups.count() > 0:
                    logger.debug(
                        'Group set: {} -> {}'.format(
                            user.username, user.groups.first().name
                        )
                    )

        logger.info(
            'Synchronized groups for {} users'.format(
                User.objects.all().count()
            )
        )
