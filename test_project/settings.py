#
# Copyright (c) 2019-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=wildcard-import, unused-wildcard-import
# pylint: disable=invalid-name, protected-access, wrong-import-position

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# do this only when runnning locally (test, pylint, runserver_plus, etc)
if not os.environ.get("RUNNING_AS_CONTAINER"):
    # site-packages/tcms_settings_dir/ must be before ./tcms_settings_dir/
    # so we can load multi_tenant.py first!
    home_dir = os.path.expanduser("~")
    removed_paths = []
    for a_path in sys.path:
        if a_path.startswith(home_dir) and a_path.find("site-packages") == -1:
            removed_paths.append(a_path)

    for a_path in removed_paths:
        sys.path.remove(a_path)

    # re add them again
    sys.path.extend(removed_paths)

    from importlib.metadata import Distribution, DistributionFinder

    # pretend this is a plugin during testing & development
    # IT NEEDS TO BE BEFORE the wildcard import below !!!
    # .egg-info/ directory will mess up with this
    class FakePluginFinder(DistributionFinder):  # pylint: disable=nested-class-found
        class FakeDistribution(Distribution):  # pylint: disable=nested-class-found
            def read_text(self, filename):
                if filename == "METADATA":
                    return """Name: github/marketplace
Version: 0.1
"""
                if filename == "entry_points.txt":
                    return """
[kiwitcms.plugins]
github/marketplace=tcms_github_marketplace
"""

                return ""

            def locate_file(self, path):
                raise RuntimeError("This distribution has no file system")

        def find_distributions(self, context=DistributionFinder.Context()):
            yield self.FakeDistribution()

    sys.meta_path.append(FakePluginFinder())

    from tcms.settings.product import *

    # check for a clean devel environment
    if os.path.exists(os.path.join(BASE_DIR, "kiwitcms_github_marketplace.egg-info")):
        print("ERORR: .egg-info/ directories mess up plugin loading code in devel mode")
        sys.exit(1)

    # import the settings which automatically get distributed with this package
    marketplace_settings = os.path.join(BASE_DIR, "tcms_settings_dir", "marketplace.py")

    # Kiwi TCMS loads extra settings in the same way using exec()
    exec(  # pylint: disable=exec-used
        open(marketplace_settings, "rb").read(),  # pylint: disable=consider-using-with
        globals(),
    )

    # these are enabled only for testing purposes
    DEBUG = True
    TEMPLATE_DEBUG = True
    LOCALE_PATHS = [os.path.join(BASE_DIR, "tcms_github_marketplace", "locale")]

    DATABASES["default"].update(  # pylint: disable=objects-update-used
        {
            "NAME": "test_project",
            "USER": "kiwi",
            "PASSWORD": "kiwi",
            "HOST": "localhost",
            "OPTIONS": {},
        }
    )

    if "social_django" not in INSTALLED_APPS:
        INSTALLED_APPS.extend(
            [
                "social_django",
            ]
        )

SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_GITHUB_APP_KEY = "oauth_client_id"
SOCIAL_AUTH_GITHUB_APP_SECRET = "oauth_client_secret"

# application specific configuration
# NOTE: must be bytes, not string
KIWI_GITHUB_MARKETPLACE_SECRET = b"S3cr3t"
KIWI_FASTSPRING_SECRET = b"s3cr3t"

# this one is string
KIWI_GITHUB_PAT_FOR_CHECKING_ORGS_AND_USERNAMES = "check-me"

# used for creating new accounts
QUAY_IO_TOKEN = os.getenv("QUAY_IO_TOKEN")

# used for creating pull tokens
GEMFURY_API_TOKEN = os.getenv("GEMFURY_API_TOKEN")

# Allows us to hook-up kiwitcms-django-plugin at will
TEST_RUNNER = os.environ.get("DJANGO_TEST_RUNNER", "django.test.runner.DiscoverRunner")

# only for testing
ALLOWED_HOSTS.append(  # noqa: F821 pylint: disable=used-before-assignment
    "testing.example.bg"
)
