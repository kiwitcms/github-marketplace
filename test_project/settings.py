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
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'tcms_github_marketplace',
]

ROOT_URLCONF = 'test_project.urls'

# application specific configuration
KIWI_GITHUB_MARKETPLACE_SECRET = 'S3cr3t'
