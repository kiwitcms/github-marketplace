# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=undefined-variable

if "tcms_github_marketplace.api" not in MODERNRPC_METHODS_MODULES:  # noqa: F821
    MODERNRPC_METHODS_MODULES.append("tcms_github_marketplace.api")  # noqa: F821

if "django.contrib.postgres" not in INSTALLED_APPS:  # noqa: F821
    INSTALLED_APPS.append("django.contrib.postgres")  # noqa: F821
