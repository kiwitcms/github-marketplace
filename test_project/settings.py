# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

# these are enabled only for testing purposes
DEBUG = True
TEMPLATE_DEBUG = True
SECRET_KEY = '7d09f358-6609-11e9-8140-34363b8604e2'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test_project',
        'USER': 'kiwi',
        'PASSWORD': 'kiwi',
        'HOST': 'localhost',
        'OPTIONS': {},
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'social_django',

    'tcms_github_marketplace',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

STATIC_URL = '/static/'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

ROOT_URLCONF = 'test_project.urls'

SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_GITHUB_KEY = 'oauth_client_id'
SOCIAL_AUTH_GITHUB_SECRET = 'oauth_client_secret'

# application specific configuration
# NOTE: must be bytes, not string
KIWI_GITHUB_MARKETPLACE_SECRET = b'S3cr3t'
