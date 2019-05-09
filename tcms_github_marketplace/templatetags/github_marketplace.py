# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def pretty_json(value):
    result = json.dumps(value, indent=4).strip()
    return mark_safe(result)
