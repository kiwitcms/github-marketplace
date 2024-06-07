# Copyright (c) 2019 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def pretty_json(value):
    result = json.dumps(value, indent=4).strip()
    return mark_safe(result)
