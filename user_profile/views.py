from django.conf import settings
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Projectroles dependency
from projectroles.views import LoggedInPermissionMixin

User = auth.get_user_model()


# TODO: Add rule perm check
class UserDetailView(LoginRequiredMixin, LoggedInPermissionMixin, TemplateView):
    template_name = 'user_profile/detail.html'
    permission_required = 'user_profile.view_detail'

