"""Ajax API views for the appalerts app"""

from rest_framework.response import Response

# Projectroles dependency
from projectroles.views_ajax import SODARBaseAjaxView

from appalerts.models import AppAlert


class AppAlertStatusAjaxView(SODARBaseAjaxView):
    """View to get app alert status for user"""

    permission_required = 'appalerts.view_alerts'

    def get(self, request, **kwargs):
        # HACK: Manually refuse access to anonymous as this view is an exception
        if not request.user or request.user.is_anonymous:
            return Response({'detail': 'Anonymous access denied'}, status=401)
        return Response(
            {
                'alerts': AppAlert.objects.filter(
                    user=request.user, active=True
                ).count()
            },
            status=200,
        )


class AppAlertDismissAjaxView(SODARBaseAjaxView):
    """View to handle app alert dismissal in UI"""

    permission_required = 'appalerts.view_alerts'

    def post(self, request, **kwargs):
        # HACK: Manually refuse access to anonymous as this view is an exception
        if not request.user or request.user.is_anonymous:
            return Response({'detail': 'Anonymous access denied'}, status=401)
        alerts = AppAlert.objects.filter(user=request.user, active=True)
        if kwargs.get('appalert'):
            alerts = alerts.filter(sodar_uuid=kwargs['appalert'])
        if not alerts:
            return Response({'detail': 'Not found'}, status=404)
        for alert in alerts:
            alert.active = False
            alert.save()
        return Response({'detail': 'OK'}, status=200)
