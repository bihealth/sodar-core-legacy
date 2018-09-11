from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Projectroles dependency
from projectroles.views import LoggedInPermissionMixin

User = auth.get_user_model()


class UserDetailView(LoginRequiredMixin, LoggedInPermissionMixin, TemplateView):
    template_name = 'userprofile/detail.html'
    permission_required = 'userprofile.view_detail'
