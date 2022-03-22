"""Factory Boy factory classes for the bgjobs app"""

import factory
from bgjobs.models import BackgroundJob


class BackgroundJobFactory(factory.django.DjangoModelFactory):
    """Factory for BackgroundJobFactory model."""

    class Meta:
        model = BackgroundJob

    # Can't set this because of circular dependency.
    # factory.SubFactory(ProjectFactory)
    project = None
    user = None  # Wait for SODAR core to offer a UserFactory
    job_type = 'type'
