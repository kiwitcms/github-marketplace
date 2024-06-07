# Copyright (c) 2022 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.conf import settings
from django.core import checks


def quay_io_token(app_configs, **kwargs):  # pylint: disable=unused-argument
    if not hasattr(settings, "QUAY_IO_TOKEN") or not settings.QUAY_IO_TOKEN:
        return [
            checks.Error(
                msg="settings.QUAY_IO_TOKEN is not defined!",
                hint=("This variable is mandatory"),
            )
        ]

    return []
