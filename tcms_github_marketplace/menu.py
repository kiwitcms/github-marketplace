# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


# Follows the format of ``tcms.settings.common.MENU_ITEMS``
MENU_ITEMS = [
    (_("Subscriptions"), reverse_lazy("github_marketplace_plans")),
]
