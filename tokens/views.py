import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic.edit import DeleteView, FormView
from django.views.generic.list import ListView
from django.urls import reverse
from knox.models import AuthToken

# Projectroles dependency
from projectroles.views import LoggedInPermissionMixin

from tokens.forms import UserTokenCreateForm


# Local constants
TOKEN_CREATE_MSG = 'Token created.'
TOKEN_DELETE_MSG = 'Token deleted.'


class UserTokenListView(LoginRequiredMixin, LoggedInPermissionMixin, ListView):
    model = AuthToken
    permission_required = 'tokens.access'
    template_name = 'tokens/token_list.html'

    def get_queryset(self):
        """Only allow access to this user's query set."""
        return AuthToken.objects.filter(user=self.request.user).order_by('-pk')


class UserTokenCreateView(
    LoginRequiredMixin, LoggedInPermissionMixin, FormView
):
    form_class = UserTokenCreateForm
    permission_required = 'tokens.access'
    template_name = 'tokens/token_create.html'

    def form_valid(self, form):
        ttl = datetime.timedelta(hours=form.clean().get('ttl')) or None
        context = self.get_context_data()
        _, context['token'] = AuthToken.objects.create(self.request.user, ttl)
        messages.success(self.request, TOKEN_CREATE_MSG)
        return render(self.request, 'tokens/token_create_success.html', context)


class UserTokenDeleteView(
    LoginRequiredMixin, LoggedInPermissionMixin, DeleteView
):
    model = AuthToken
    permission_required = 'tokens.access'
    template_name = 'tokens/token_confirm_delete.html'

    def get_success_url(self):
        messages.success(self.request, TOKEN_DELETE_MSG)
        return reverse('tokens:list')

    def get_queryset(self):
        """Only allow access to this user's query set."""
        return AuthToken.objects.filter(user=self.request.user)
