import uuid

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

# Projectroles dependency
from projectroles.models import Project

# Access Django user model
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class BaseCacheItem(models.Model):
    """abstract class representing a cached item"""

    class Meta:
        abstract = True
        unique_together = (('project', 'app_name', 'name'),)

    #: Project in which the item belongs
    project = models.ForeignKey(
        Project,
        related_name='cached_items',
        help_text='Project in which the item belongs',
        null=True,
        blank=True,
    )

    #: App name
    app_name = models.CharField(max_length=255, help_text='App name')

    #: Identifier for the item given by the data setting app
    name = models.CharField(
        max_length=255,
        help_text='Name or title of the item given by the data setting app',
    )

    #: DateTime of the update
    date_modified = models.DateTimeField(
        auto_now_add=True, help_text='DateTime of the update'
    )

    #: User who updated the item
    user = models.ForeignKey(
        AUTH_USER_MODEL, help_text='User who updated the item'
    )

    #: UUID for the item
    sodar_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text='Item SODAR UUID'
    )

    def __str__(self):
        return '{}: {}: {}'.format(self.name, self.project.title)

    def __repr__(self):
        return '{}: {}: {}'.format(self.name, self.project.title, self.app_name)


class JsonCacheItem(BaseCacheItem):
    """class representing a cached item in JSON format"""

    #: Cached data as JSON
    data = JSONField(default=dict, help_text='Cached data as JSON')

    def __str__(self):
        return '{}: {}: {}'.format(self.project.title, self.name, self.data)

    def __repr__(self):
        values = (self.project.title, self.name, self.app_name)
        return 'JsonCacheItem({})'.format(', '.join(repr(v) for v in values))
