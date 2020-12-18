from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views import defaults as default_views
from django.views.generic import TemplateView


import django_saml2_auth.views
from projectroles.views import HomeView


urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(
        r'^about/$',
        TemplateView.as_view(template_name='pages/about.html'),
        name='about',
    ),
    # Django Admin, use {% url 'admin:index' %}
    url(settings.ADMIN_URL, admin.site.urls),
    # Login and logout
    url(
        r'^login/$',
        auth_views.LoginView.as_view(template_name='users/login.html'),
        name='login',
    ),
    url(r'^logout/$', auth_views.logout_then_login, name='logout'),
    # Auth
    url(r'api/auth/', include('knox.urls')),
    # Projectroles URLs
    url(r'^project/', include('projectroles.urls')),
    # Timeline URLs
    url(r'^timeline/', include('timeline.urls')),
    # Filesfolders URLs
    url(r'^files/', include('filesfolders.urls')),
    # django-db-file-storage URLs (obfuscated for users)
    url(r'^naFieng1Lai8heg2/', include('db_file_storage.urls')),
    # User Profile URLs
    url(r'^user/', include('userprofile.urls')),
    # Admin Alerts URLs
    url(r'^alerts/', include('adminalerts.urls')),
    # Site Info URLs
    url(r'^siteinfo/', include('siteinfo.urls')),
    # API Tokens URLs
    url(r'^tokens/', include('tokens.urls')),
    # Background Jobs URLs
    url(r'^bgjobs/', include('bgjobs.urls')),
    # Data Cache app
    url(r'^cache/', include('sodarcache.urls')),
    # Example project app URLs
    url(r'^examples/project/', include('example_project_app.urls')),
    # Example site app URLs
    url(r'^examples/site/', include('example_site_app.urls')),
    # These are the SAML2 related URLs. You can change "^saml2_auth/" regex to
    # any path you want, like "^sso_auth/", "^sso_login/", etc. (required)
    url(r'^saml2_auth/', include('django_saml2_auth.urls')),
    # The following line will replace the default user login with SAML2 (optional)
    # If you want to specific the after-login-redirect-URL, use parameter "?next=/the/path/you/want"
    # with this view.
    url(r'^sso/login/$', django_saml2_auth.views.signin),
    # The following line will replace the admin login with SAML2 (optional)
    # If you want to specific the after-login-redirect-URL, use parameter "?next=/the/path/you/want"
    # with this view.
    url(r'^sso/admin/login/$', django_saml2_auth.views.signin),
    # The following line will replace the default user logout with the signout page (optional)
    url(r'^sso/logout/$', django_saml2_auth.views.signout),
    # The following line will replace the default admin user logout with the signout page (optional)
    url(r'^sso/admin/logout/$', django_saml2_auth.views.signout),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(
            r'^400/$',
            default_views.bad_request,
            kwargs={'exception': Exception('Bad Request!')},
        ),
        url(
            r'^403/$',
            default_views.permission_denied,
            kwargs={'exception': Exception('Permission Denied')},
        ),
        url(
            r'^404/$',
            default_views.page_not_found,
            kwargs={'exception': Exception('Page not Found')},
        ),
        url(r'^500/$', default_views.server_error),
    ]

    urlpatterns += staticfiles_urlpatterns()

    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            url(r'^__debug__/', include(debug_toolbar.urls))
        ] + urlpatterns
