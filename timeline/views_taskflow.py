"""Taskflow API views for the timeline app"""

from rest_framework.response import Response

# Projectroles dependency
from projectroles.views_taskflow import BaseTaskflowAPIView

from timeline.models import ProjectEvent


class TaskflowEventStatusSetAPIView(BaseTaskflowAPIView):
    def post(self, request):
        try:
            tl_event = ProjectEvent.objects.get(
                sodar_uuid=request.data['event_uuid']
            )

        except ProjectEvent.DoesNotExist:
            return Response('Timeline event not found', status=404)

        try:
            tl_event.set_status(
                status_type=request.data['status_type'],
                status_desc=request.data['status_desc'],
                extra_data=request.data['extra_data']
                if 'extra_data' in request.data
                else None,
            )

        except TypeError:
            return Response('Invalid status type', status=400)

        return Response('ok', status=200)
