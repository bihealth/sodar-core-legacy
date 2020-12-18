"""
Django settings for the SODAR Core Example Site project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
import environ

from projectroles.constants import get_sodar_constants


SITE_PACKAGE = 'example_site'

ROOT_DIR = environ.Path(__file__) - 3
APPS_DIR = ROOT_DIR.path(SITE_PACKAGE)

# Load operating system environment variables and then prepare to use them
env = environ.Env()

# .env file, should load only in development environment
READ_DOT_ENV_FILE = env.bool('DJANGO_READ_DOT_ENV_FILE', default=False)

if READ_DOT_ENV_FILE:
    # Operating System Environment variables have precedence over variables
    # defined in the .env file, that is to say variables from the .env files
    # will only be used if not defined as environment variables.
    env_file = str(ROOT_DIR.path('.env'))
    env.read_env(env_file)

# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['*'])

# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    # Default Django apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Useful template tags
    # 'django.contrib.humanize',
    # Admin
    'django.contrib.admin',
]
THIRD_PARTY_APPS = [
    'crispy_forms',  # Form layouts
    'rules.apps.AutodiscoverRulesConfig',  # Django rules engine
    'djangoplugins',  # Django plugins
    'pagedown',  # For markdown
    'markupfield',  # For markdown
    'rest_framework',  # For API views
    'knox',  # For token auth
    'docs',  # For the online user documentation/manual
    'db_file_storage',  # For filesfolders
    'dal',  # For user search combo box
    'dal_select2',
    'django_saml2_auth',  # SAML2 support
]

# Project apps
LOCAL_APPS = [
    # Custom users app
    'example_site.users.apps.UsersConfig',
    # SODAR Projectroles app
    'projectroles.apps.ProjectrolesConfig',
    # SODAR Timeline app
    'timeline.apps.TimelineConfig',
    # SODAR Filesfolders app
    'filesfolders.apps.FilesfoldersConfig',
    # User Profile site app
    'userprofile.apps.UserprofileConfig',
    # Admin Alerts site app
    'adminalerts.apps.AdminalertsConfig',
    # Site Info site app
    'siteinfo.apps.SiteinfoConfig',
    # API Tokens site app
    'tokens.apps.TokensConfig',
    # SODAR Taskflow backend app
    'taskflowbackend.apps.TaskflowbackendConfig',
    # Background Jobs app
    'bgjobs.apps.BgjobsConfig',
    # External Data Cache app
    'sodarcache.apps.SodarcacheConfig',
    # Example project app
    'example_project_app.apps.ExampleProjectAppConfig',
    # Example site app
    'example_site_app.apps.ExampleSiteAppConfig',
    # Example backend app
    'example_backend_app.apps.ExampleBackendAppConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# MIGRATIONS CONFIGURATION
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {'sites': 'example_site.contrib.sites.migrations'}

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool('DJANGO_DEBUG', False)

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
FIXTURE_DIRS = (str(APPS_DIR.path('fixtures')),)

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env(
    'DJANGO_EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_SENDER = env('EMAIL_SENDER', default='noreply@example.com')
EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', default='')

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
ADMINS = [("""Admin User""", 'admin.user@example.com')]

# See: https://docs.djangoproject.com/en/1.11/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/1.11/ref/settings/#databases
# Uses django-environ to accept uri format
# See: https://django-environ.readthedocs.io/en/latest/#supported-types
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres:///sodar_core')
}
DATABASES['default']['ATOMIC_REQUESTS'] = False

# Set django-db-file-storage as the default storage (for filesfolders)
DEFAULT_FILE_STORAGE = 'db_file_storage.storage.DatabaseFileStorage'


# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Berlin'

# See: https://docs.djangoproject.com/en/1.11/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# See: https://docs.djangoproject.com/en/1.11/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/1.11/ref/settings/#use-i18n
USE_I18N = False

# See: https://docs.djangoproject.com/en/1.11/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/1.11/ref/settings/#use-tz
USE_TZ = True

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/1.11/ref/settings/#templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(APPS_DIR.path('templates'))],
        'OPTIONS': {
            'debug': DEBUG,
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                # Site context processors
                'projectroles.context_processors.urls_processor',
            ],
        },
    }
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
STATIC_ROOT = str(ROOT_DIR('staticfiles'))
STATIC_URL = '/static/'

STATICFILES_DIRS = [str(APPS_DIR.path('static'))]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
MEDIA_ROOT = str(APPS_DIR('media'))
MEDIA_URL = '/media/'

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# PASSWORD STORAGE SETTINGS
# ------------------------------------------------------------------------------
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

# PASSWORD VALIDATION
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'UserAttributeSimilarityValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'MinimumLengthValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'CommonPasswordValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'NumericPasswordValidator'
    },
]

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    'rules.permissions.ObjectPermissionBackend',  # For rules
    'django.contrib.auth.backends.ModelBackend',
]

# Custom user app defaults
AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = 'slugify.slugify'

# Location of root django.contrib.admin URL, use {% url 'admin:index' %}
ADMIN_URL = r'^admin/'


# Celery
# ------------------------------------------------------------------------------
if USE_TZ:
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-timezone
    CELERY_TIMEZONE = TIME_ZONE
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_url
CELERY_BROKER_URL = env.str('CELERY_BROKER_URL', 'redis://localhost:6379/0')
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_backend
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-accept_content
CELERY_ACCEPT_CONTENT = ['json']
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-task_serializer
CELERY_TASK_SERIALIZER = 'json'
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_serializer
CELERY_RESULT_SERIALIZER = 'json'
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-time-limit
CELERYD_TASK_TIME_LIMIT = 5 * 60
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-soft-time-limit
CELERYD_TASK_SOFT_TIME_LIMIT = 60


# Django REST framework default auth classes
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'knox.auth.TokenAuthentication',
    )
}

# Knox settings
TOKEN_TTL = None

# Settings for HTTP AuthBasic
BASICAUTH_REALM = 'Log in with user@DOMAIN and your password.'
BASICAUTH_DISABLE = False


# LDAP configuration
# ------------------------------------------------------------------------------

# Enable LDAP if configured
ENABLE_LDAP = env.bool('ENABLE_LDAP', False)
ENABLE_LDAP_SECONDARY = env.bool('ENABLE_LDAP_SECONDARY', False)

if ENABLE_LDAP:
    import itertools
    import ldap
    from django_auth_ldap.config import LDAPSearch

    # Default values
    LDAP_DEFAULT_CONN_OPTIONS = {ldap.OPT_REFERRALS: 0}
    LDAP_DEFAULT_FILTERSTR = '(sAMAccountName=%(user)s)'
    LDAP_DEFAULT_ATTR_MAP = {
        'first_name': 'givenName',
        'last_name': 'sn',
        'email': 'mail',
    }

    # Primary LDAP server
    AUTH_LDAP_SERVER_URI = env.str('AUTH_LDAP_SERVER_URI', None)
    AUTH_LDAP_BIND_DN = env.str('AUTH_LDAP_BIND_DN', None)
    AUTH_LDAP_BIND_PASSWORD = env.str('AUTH_LDAP_BIND_PASSWORD', None)
    AUTH_LDAP_CONNECTION_OPTIONS = LDAP_DEFAULT_CONN_OPTIONS

    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        env.str('AUTH_LDAP_USER_SEARCH_BASE', None),
        ldap.SCOPE_SUBTREE,
        LDAP_DEFAULT_FILTERSTR,
    )
    AUTH_LDAP_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
    AUTH_LDAP_USERNAME_DOMAIN = env.str('AUTH_LDAP_USERNAME_DOMAIN', None)
    AUTH_LDAP_DOMAIN_PRINTABLE = env.str(
        'AUTH_LDAP_DOMAIN_PRINTABLE', AUTH_LDAP_USERNAME_DOMAIN
    )

    AUTHENTICATION_BACKENDS = tuple(
        itertools.chain(
            ('projectroles.auth_backends.PrimaryLDAPBackend',),
            AUTHENTICATION_BACKENDS,
        )
    )

    # Secondary LDAP server (optional)
    if ENABLE_LDAP_SECONDARY:
        AUTH_LDAP2_SERVER_URI = env.str('AUTH_LDAP2_SERVER_URI', None)
        AUTH_LDAP2_BIND_DN = env.str('AUTH_LDAP2_BIND_DN', None)
        AUTH_LDAP2_BIND_PASSWORD = env.str('AUTH_LDAP2_BIND_PASSWORD', None)
        AUTH_LDAP2_CONNECTION_OPTIONS = LDAP_DEFAULT_CONN_OPTIONS

        AUTH_LDAP2_USER_SEARCH = LDAPSearch(
            env.str('AUTH_LDAP2_USER_SEARCH_BASE', None),
            ldap.SCOPE_SUBTREE,
            LDAP_DEFAULT_FILTERSTR,
        )
        AUTH_LDAP2_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
        AUTH_LDAP2_USERNAME_DOMAIN = env.str('AUTH_LDAP2_USERNAME_DOMAIN')
        AUTH_LDAP2_DOMAIN_PRINTABLE = env.str(
            'AUTH_LDAP2_DOMAIN_PRINTABLE', AUTH_LDAP2_USERNAME_DOMAIN
        )

        AUTHENTICATION_BACKENDS = tuple(
            itertools.chain(
                ('projectroles.auth_backends.SecondaryLDAPBackend',),
                AUTHENTICATION_BACKENDS,
            )
        )


# Logging
# ------------------------------------------------------------------------------


def set_logging(debug):
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            }
        },
        'loggers': {
            'projectroles': {
                'level': 'DEBUG' if debug else 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'taskflowbackend': {
                'level': 'DEBUG' if debug else 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'sodarcache': {
                'level': 'DEBUG' if debug else 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }


LOGGING = set_logging(DEBUG)


# General site settings
# ------------------------------------------------------------------------------

SITE_TITLE = 'SODAR Core Example Site'
SITE_SUBTITLE = env.str('SITE_SUBTITLE', 'Beta')
SITE_INSTANCE_TITLE = env.str('SITE_INSTANCE_TITLE', 'SODAR Core Example')


# Local App Settings
# ------------------------------------------------------------------------------


# Plugin settings
ENABLED_BACKEND_PLUGINS = env.list(
    'ENABLED_BACKEND_PLUGINS', None, ['timeline_backend', 'example_backend_app']
)

# SODAR API settings
SODAR_API_DEFAULT_VERSION = '0.1'
SODAR_API_ALLOWED_VERSIONS = [SODAR_API_DEFAULT_VERSION]
SODAR_API_MEDIA_TYPE = 'application/your.application+json'
SODAR_API_DEFAULT_HOST = env.url(
    'SODAR_API_DEFAULT_HOST', 'http://0.0.0.0:8000'
)


# Projectroles app settings

# Remote access mode: SOURCE or TARGET
PROJECTROLES_SITE_MODE = env.str('PROJECTROLES_SITE_MODE', 'SOURCE')

# Enable or disable project creation if site is in TARGET mode
PROJECTROLES_TARGET_CREATE = env.bool('PROJECTROLES_TARGET_CREATE', True)

# Username of default admin for when regular users cannot be assigned to a task
PROJECTROLES_DEFAULT_ADMIN = env.str('PROJECTROLES_DEFAULT_ADMIN', 'admin')

# Allow showing and synchronizing local non-admin users
PROJECTROLES_ALLOW_LOCAL_USERS = env.bool(
    'PROJECTROLES_ALLOW_LOCAL_USERS', False
)

# General projectroles settings
PROJECTROLES_DISABLE_CATEGORIES = env.bool(
    'PROJECTROLES_DISABLE_CATEGORIES', False
)
PROJECTROLES_INVITE_EXPIRY_DAYS = env.int('PROJECTROLES_INVITE_EXPIRY_DAYS', 14)
PROJECTROLES_SEND_EMAIL = env.bool('PROJECTROLES_SEND_EMAIL', False)
PROJECTROLES_EMAIL_SENDER_REPLY = env.bool(
    'PROJECTROLES_EMAIL_SENDER_REPLY', False
)
PROJECTROLES_ENABLE_SEARCH = True

# Optional projectroles settings
# PROJECTROLES_SECRET_LENGTH = 32
# PROJECTROLES_HELP_HIGHLIGHT_DAYS = 7
# PROJECTROLES_SEARCH_PAGINATION = 5
# Support for viewing the site in "kiosk mode" (under work, experimental)
# PROJECTROLES_KIOSK_MODE = env.bool('PROJECTROLES_KIOSK_MODE', False)

PROJECTROLES_HIDE_APP_LINKS = env.list('PROJECTROLES_HIDE_APP_LINKS', None, [])

# Set limit for delegate roles per project (if 0, no limit is applied)
PROJECTROLES_DELEGATE_LIMIT = env.int('PROJECTROLES_DELEGATE_LIMIT', 1)

# Warn about unsupported browsers (IE)
PROJECTROLES_BROWSER_WARNING = True

# Disable default CDN JS/CSS includes to replace with your local files
PROJECTROLES_DISABLE_CDN_INCLUDES = env.bool(
    'PROJECTROLES_DISABLE_CDN_INCLUDES', False
)

# Paths/URLs to optional global includes to supplement/replace default ones
PROJECTROLES_CUSTOM_JS_INCLUDES = env.list(
    'PROJECTROLES_CUSTOM_JS_INCLUDES', None, []
)
PROJECTROLES_CUSTOM_CSS_INCLUDES = env.list(
    'PROJECTROLES_CUSTOM_CSS_INCLUDES', None, []
)


# Bgjobs app settings
BGJOBS_PAGINATION = env.int('BGJOBS_PAGINATION', 15)


# Timeline app settings
TIMELINE_PAGINATION = 15


# Filesfolders app settings
FILESFOLDERS_MAX_UPLOAD_SIZE = env.int('FILESFOLDERS_MAX_UPLOAD_SIZE', 10485760)
FILESFOLDERS_MAX_ARCHIVE_SIZE = env.int(
    'FILESFOLDERS_MAX_ARCHIVE_SIZE', 52428800
)
FILESFOLDERS_SERVE_AS_ATTACHMENT = False
FILESFOLDERS_LINK_BAD_REQUEST_MSG = 'Invalid request'
FILESFOLDERS_SHOW_LIST_COLUMNS = True  # Custom project list column example


# Adminalerts app settings
ADMINALERTS_PAGINATION = 15


# Taskflow backend settings
TASKFLOW_SODAR_SECRET = env.str('TASKFLOW_SODAR_SECRET', 'CHANGE ME!')
TASKFLOW_TEST_MODE = False  # Important! Disallow cleanup() command by default


# SODAR constants
# SODAR_CONSTANTS = get_sodar_constants(default=True)

ENABLE_SAML = env.bool('ENABLE_SAML', False)
SAML2_AUTH = {
    # Required setting
    'SAML_CLIENT_SETTINGS': {  # Pysaml2 Saml client settings (https://pysaml2.readthedocs.io/en/latest/howto/config.html)
        'entityid': env.str(
            'SAML_CLIENT_ENTITY_ID', 'SODARcore'
        ),  # The optional entity ID string to be passed in the 'Issuer' element of authn request, if required by the IDP.
        'entitybaseurl': env.str(
            'SAML_CLIENT_ENTITY_URL', 'https://localhost:8000'
        ),
        'metadata': {
            'local': [
                env.str(
                    'SAML_CLIENT_METADATA_FILE', 'metadata.xml'
                ),  # The auto(dynamic) metadata configuration URL of SAML2
            ],
        },
        "service": {
            'sp': {
                'idp': env.str(
                    'SAML_CLIENT_IPD',
                    'https://sso.hpc.bihealth.org/auth/realms/cubi',
                ),
                # Keycloak expects client signature
                'authn_requests_signed': 'true',
                # Enforce POST binding which is required by keycloak
                'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
            },
        },
        'key_file': env.str('SAML_CLIENT_KEY_FILE', 'key.pem'),
        'cert_file': env.str('SAML_CLIENT_CERT_FILE', 'cert.pem'),
        'xmlsec_binary': env.str('SAML_CLIENT_XMLSEC1', '/usr/bin/xmlsec1'),
        'encryption_keypairs': [
            {
                'key_file': env.str('SAML_CLIENT_KEY_FILE', 'key.pem'),
                'cert_file': env.str('SAML_CLIENT_CERT_FILE', 'cert.pem'),
            }
        ],
    },
    'DEFAULT_NEXT_URL': '/',  # Custom target redirect URL after the user get logged in. Default to /admin if not set. This setting will be overwritten if you have parameter ?next= specificed in the login URL.
    # # Optional settings below
    # 'NEW_USER_PROFILE': {
    #     'USER_GROUPS': [],  # The default group name when a new user logs in
    #     'ACTIVE_STATUS': True,  # The default active status for new users
    #     'STAFF_STATUS': True,  # The staff status for new users
    #     'SUPERUSER_STATUS': False,  # The superuser status for new users
    # },
    # 'ATTRIBUTES_MAP': {  # Change Email/UserName/FirstName/LastName to corresponding SAML2 userprofile attributes.
    #     'email': 'Email',
    #     'username': 'UserName',
    #     'first_name': 'FirstName',
    #     'last_name': 'LastName',
    # },
    # 'TRIGGER': {
    #     'FIND_USER': 'path.to.your.find.user.hook.method',
    #     'NEW_USER': 'path.to.your.new.user.hook.method',
    #     'CREATE_USER': 'path.to.your.create.user.hook.method',
    #     'BEFORE_LOGIN': 'path.to.your.login.hook.method',
    # },
    # 'ASSERTION_URL': 'https://cubi5.bihealth.org:8000',  # Custom URL to validate incoming SAML requests against
}
