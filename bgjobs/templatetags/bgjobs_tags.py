from django import template

from ..models import BackgroundJob
from ..plugins import BackgroundJobsPluginPoint

register = template.Library()


@register.simple_tag
def get_details_backgroundjobs(project):
    """Return active background jobs for the project details page"""
    return BackgroundJob.objects.filter(project=project).order_by('-pk')[:5]


@register.filter
def specialize_job(bg_job):
    """Given a ``BackgroundJob``, return the specialized job if any.

    Specialized job models are linked back to the ``BackgroundJob`` through a
    ``OneToOneField`` named ``bg_job``.
    """
    # Global map from job specialization name to model class.
    job_specs = {}
    # Setup the global map.
    for plugin in BackgroundJobsPluginPoint.get_plugins():
        assert not (
            set(plugin.job_specs) & set(job_specs)
        ), 'Registering model twice!'
        job_specs.update(plugin.job_specs)

    klass = job_specs.get(bg_job.job_type)
    if not klass:
        return bg_job
    else:
        try:
            return klass.objects.get(bg_job=bg_job)
        except klass.DoesNotExist:
            return bg_job


# Originally from dict.py in varfish-web (see issue #97)
@register.filter
def keyvalue(data, key):
    if hasattr(data, 'get'):
        return data.get(key)
    else:
        return data[key]
