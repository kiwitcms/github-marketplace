# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

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
