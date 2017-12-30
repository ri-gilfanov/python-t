from .common import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INTERNAL_IPS = ['localhost', '127.0.0.1']  # для debug_toolbar


INSTALLED_APPS.extend([
    'debug_toolbar',
])


MIDDLEWARE.extend([
    'debug_toolbar.middleware.DebugToolbarMiddleware',
])


DATABASES = {
    'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'dev_database',
    'USER': 'dev_user',
    'PASSWORD': 'dev_password',
    }
}
