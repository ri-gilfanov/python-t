import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'dev_secret_key'

SITE_NAME = 'Питон'

SITE_DESCRIPTION = 'поставщик инженерных систем в г. Тюмени'


DATABASES = {
    'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'dev_database',
    'USER': 'dev_user',
    'PASSWORD': 'dev_password',
    }
}

INSTALLED_APPS = [
    # из фреймворка
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    # из окружения
    'ckeditor',
    'ckeditor_uploader',
    'mptt',
    'mail_templated',
    'mathfilters',
    'nested_admin',
    # из проекта
    'core',
    'users',
    'shop',
    'search',
    'pages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_info',
                'shop.context_processors.get_category_tree',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'users.User'

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Asia/Yekaterinburg'

USE_I18N = True

USE_L10N = True

USE_TZ = True


MEDIA_ROOT = '%s/files/media/' % (BASE_DIR)

MEDIA_URL = '/media/'

STATIC_ROOT = '%s/files/static/' % (BASE_DIR)

STATIC_URL = '/static/'





CKEDITOR_JQUERY_URL = '/static/jquery-3.1.1.min.js'


CKEDITOR_UPLOAD_PATH = 'images/'

# Группировка изображений по папкам пользователей и разграниченный доступ,
# названия папок по полю username
CKEDITOR_RESTRICT_BY_USER = True

# Бэкенд для создания миниатюрок изображений
CKEDITOR_IMAGE_BACKEND = 'pillow'

# Просмотр изображений с группировкой по папкам
CKEDITOR_BROWSE_SHOW_DIRS = True

# Загрузка файлов, отличных от изображений
CKEDITOR_ALLOW_NONIMAGE_FILES = False


CKEDITOR_CONFIGS = {
        'default': {
        'resize_dir': 'both',
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Source','Maximize','ShowBlocks','DocProps','Preview',],
            ['Cut','Copy','Paste','PasteText','PasteFromWord','-','Undo','Redo',],
            ['Find','Replace','-','SelectAll','-','SpellChecker',],
            ['Link','Unlink','Anchor'],
            ['Image', 'Youtube', 'Table',],
            '/',
            ['Format'],
            ['Bold','Italic','Underline'],
            ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],
            ['NumberedList','BulletedList','-','Outdent','Indent'],
            ['Subscript','Superscript','-','Blockquote',],
            ['RemoveFormat'],
        ],
        'width': '100%',
        'format_tags': 'p;h2;h3;h4;h5;h6;pre;address;div',
        'allowedContent': True,  # разрешение на вставку скриптов
        'contentsCss': ['/sf/core/common.css', ],
        'extraPlugins': 'youtube',
    },
}
AWS_QUERYSTRING_AUTH = False



LOGIN_URL = '/sign_in/'



EMAIL_HOST = 'dev_email_host'
EMAIL_HOST_USER = "dev_email_host_user"
EMAIL_HOST_PASSWORD = "dev_email_host_password"
EMAIL_USE_SSL = True
EMAIL_PORT = 465
