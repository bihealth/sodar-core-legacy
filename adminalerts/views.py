"""UI views for the adminalerts app"""

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import (
    DetailView,
    UpdateView,
    CreateView,
    DeleteView,
    ListView,
)
from django.views.generic.edit import ModelFormMixin

# Projectroles dependency
from projectroles.views import (
    LoggedInPermissionMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
)

from adminalerts.forms import AdminAlertForm
from adminalerts.models import AdminAlert


DEFAULT_PAGINATION = 15


# Listing/details views --------------------------------------------------------


class AdminAlertListView(LoggedInPermissionMixin, ListView):
    """Alert list view"""

    permission_required = 'adminalerts.create_alert'
    template_name = 'adminalerts/alert_list.html'
    model = AdminAlert
    paginate_by = getattr(
        settings, 'ADMINALERTS_PAGINATION', DEFAULT_PAGINATION
    )
    slug_url_kwarg = 'adminalert'
    slug_field = 'sodar_uuid'

    def get_queryset(self):
        return AdminAlert.objects.all().order_by('-pk')


class AdminAlertDetailView(
    LoggedInPermissionMixin, HTTPRefererMixin, DetailView
):
    """Alert detail view"""

    permission_required = 'adminalerts.view_alert'
    template_name = 'adminalerts/alert_detail.html'
    model = AdminAlert
    slug_url_kwarg = 'adminalert'
    slug_field = 'sodar_uuid'


# Modification views -----------------------------------------------------------


class AdminAlertModifyMixin(ModelFormMixin):
    def form_valid(self, form):
        form.save()
        form_action = 'update' if self.object else 'create'
        messages.success(self.request, 'Alert {}d.'.format(form_action))
        return redirect(reverse('adminalerts:list'))


class AdminAlertCreateView(
    LoggedInPermissionMixin,
    AdminAlertModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    CreateView,
):
    """AdminAlert creation view"""

    model = AdminAlert
    form_class = AdminAlertForm
    permission_required = 'adminalerts.create_alert'


class AdminAlertUpdateView(
    LoggedInPermissionMixin,
    AdminAlertModifyMixin,
    HTTPRefererMixin,
    CurrentUserFormMixin,
    UpdateView,
):
    """AdminAlert updating view"""

    model = AdminAlert
    form_class = AdminAlertForm
    permission_required = 'adminalerts.update_alert'
    slug_url_kwarg = 'adminalert'
    slug_field = 'sodar_uuid'


class AdminAlertDeleteView(
    LoggedInPermissionMixin, HTTPRefererMixin, DeleteView
):
    """AdminAlert deletion view"""

    model = AdminAlert
    permission_required = 'adminalerts.update_alert'
    slug_url_kwarg = 'adminalert'
    slug_field = 'sodar_uuid'

    def get_success_url(self):
        """Override for redirecting alert list view with message"""
        messages.success(self.request, 'Alert deleted.')
        return reverse('adminalerts:list')
