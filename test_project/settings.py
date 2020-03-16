# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=invalid-name, protected-access, wrong-import-position

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# site-packages/tcms_settings_dir/ must be before ./tcms_settings_dir/
# so we can load multi_tenant.py first!
if BASE_DIR in sys.path:
    sys.path.remove(BASE_DIR)
    sys.path.append(BASE_DIR)

import pkg_resources

# pretend this is a plugin during testing & development
# IT NEEDS TO BE BEFORE the wildcard import below !!!
# .egg-info/ directory will mess up with this
dist = pkg_resources.Distribution(__file__)
entry_point = pkg_resources.EntryPoint.parse('github/marketplace = tcms_github_marketplace',
                                             dist=dist)
dist._ep_map = {'kiwitcms.plugins': {'kiwitcms_tenants_devel': entry_point}}
pkg_resources.working_set.add(dist)

from tcms.settings.product import *

# check for a clean devel environment
if os.path.exists(os.path.join(BASE_DIR, "kiwitcms_github_marketplace.egg-info")):
    print("ERORR: .egg-info/ directories mess up plugin loading code in devel mode")
    sys.exit(1)


# import the settings which automatically get distributed with this package
marketplace_settings = os.path.join(
    BASE_DIR, 'tcms_settings_dir', 'marketplace.py')

# Kiwi TCMS loads extra settings in the same way using exec()
exec(  # pylint: disable=exec-used
    open(marketplace_settings, "rb").read(),
    globals()
)

# these are enabled only for testing purposes
DEBUG = True
TEMPLATE_DEBUG = True
LOCALE_PATHS = [os.path.join(BASE_DIR, 'tcms_github_marketplace', 'locale')]

DATABASES['default'].update({
    'NAME': 'test_project',
    'USER': 'kiwi',
    'PASSWORD': 'kiwi',
    'HOST': 'localhost',
    'OPTIONS': {},
})


INSTALLED_APPS.extend([
    'social_django',
])

PUBLIC_VIEWS.extend([
    'social_django.views.auth',
    'social_django.views.complete',
    'social_django.views.disconnect',
])


SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_GITHUB_KEY = 'oauth_client_id'
SOCIAL_AUTH_GITHUB_SECRET = 'oauth_client_secret'

# application specific configuration
# NOTE: must be bytes, not string
KIWI_GITHUB_MARKETPLACE_SECRET = b'S3cr3t'
