"""Ajax views for the adminalerts app"""

from django.http import HttpResponseBadRequest

from rest_framework.response import Response

# Projectroles dependency
from projectroles.views_ajax import SODARBasePermissionAjaxView

from adminalerts.models import AdminAlert


class AdminAlertActiveToggleAjaxView(SODARBasePermissionAjaxView):
    """AdminAlert acivation toggling Ajax view"""

    permission_required = 'adminalerts.update_alert'
    http_method_names = ['post']

    def post(self, request, **kwargs):
        alert_uuid = kwargs.get('adminalert', None)

        try:
            alert = AdminAlert.objects.get(sodar_uuid__exact=alert_uuid)

        except AdminAlert.DoesNotExist:
            return HttpResponseBadRequest()

        alert.active = not alert.active
        alert.save()
        return Response({'is_active': alert.active}, status=200)
